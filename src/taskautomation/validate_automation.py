#!/usr/bin/env python3
"""
Validation script for task automation system.

This script implements the "check your work" philosophy by comprehensively
validating all components of the task automation system. It serves as both
a validation tool and a demonstration of the validation capabilities.

Features:
- Validates task_utils.py module functionality
- Checks system prerequisites
- Validates existing tasks file
- Tests all validation functions
- Provides detailed reporting in human or JSON format
- Supports dry-run mode for safe operation

Usage:
    python validate_automation.py [OPTIONS]

Options:
    --format {human,json}    Output format (default: human)
    --quiet                  Suppress non-essential output
    --fix-issues            Attempt to fix detected issues (dry-run by default)
    --dry-run               Preview fixes without applying them
    --help                   Show this help message
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import traceback

# Add the parent directory to the path to import task_utils
sys.path.insert(0, str(pathlib.Path(__file__).parent))

try:
    from task_utils import (
        ROOT,
        TASKS_FILE,
        ExitCode,
        OperationResult,
        TaskInfo,
        ValidationResult,
        create_structured_error,
        get_current_datetime,
        get_git_info,
        load_tasks_file,
        output_result,
        validate_prerequisites,
        validate_task_data,
        validate_tasks_file,
        verify_operation_safety,
    )
except ImportError as e:
    print(f"✗ Failed to import task_utils: {e}")
    print("Make sure task_utils.py is properly installed and accessible.")
    sys.exit(3)


class AutomationValidator:
    """Comprehensive validator for the task automation system."""

    def __init__(self, quiet: bool = False, format_type: str = "human"):
        self.quiet = quiet
        self.format_type = format_type
        self.results = []
        self.overall_success = True

    def log_result(self, result: OperationResult) -> None:
        """Log a validation result."""
        self.results.append(result)
        if not result.success:
            self.overall_success = False

        if not self.quiet:
            output_result(result, self.format_type, self.quiet)

    def validate_module_imports(self) -> OperationResult:
        """Validate that all required modules can be imported."""
        errors = []
        warnings = []
        context = {"validation_type": "module_imports"}

        # Test critical imports
        required_modules = [
            "collections",
            "datetime",
            "enum",
            "json",
            "pathlib",
            "re",
            "shutil",
            "subprocess",
            "sys",
            "os",
        ]

        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                errors.append(f"Required module '{module_name}' not available: {e}")

        # Test task_utils specific imports
        try:
            from task_utils import (
                ID_RE,
                METADATA_RE,
                SUBTASK_RE,
                TASK_BLOCK_RE,
                format_task_block,
                parse_existing_tasks,
            )

            context["task_utils_imports"] = "success"
        except ImportError as e:
            errors.append(f"task_utils imports failed: {e}")

        return OperationResult(
            success=len(errors) == 0,
            exit_code=ExitCode.SUCCESS if len(errors) == 0 else ExitCode.SYSTEM_ERROR,
            message="Module import validation completed",
            data=context,
            errors=errors,
            warnings=warnings,
        )

    def validate_file_structure(self) -> OperationResult:
        """Validate that required files and directories exist."""
        errors = []
        warnings = []
        context = {"validation_type": "file_structure"}

        # Check required files
        required_files = [
            ROOT / "scripts" / "dev" / "task_utils.py",
            ROOT / "scripts" / "dev" / "run_tests.py",
            ROOT / "scripts" / "dev" / "create_change_entry.py",
        ]

        for file_path in required_files:
            if not file_path.exists():
                errors.append(f"Required file missing: {file_path}")
            elif not file_path.is_file():
                errors.append(f"Path exists but is not a file: {file_path}")
            else:
                context[f"found_{file_path.name}"] = True

        # Check optional files
        optional_files = [TASKS_FILE]
        for file_path in optional_files:
            if not file_path.exists():
                warnings.append(f"Optional file missing: {file_path}")
            else:
                context[f"found_{file_path.name}"] = True

        # Check required directories
        required_dirs = [
            ROOT / "docs",
            ROOT / "scripts" / "dev",
            ROOT / "docs" / "planning",
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                errors.append(f"Required directory missing: {dir_path}")
            elif not dir_path.is_dir():
                errors.append(f"Path exists but is not a directory: {dir_path}")
            else:
                context[f"found_{dir_path.name}"] = True

        return OperationResult(
            success=len(errors) == 0,
            exit_code=ExitCode.SUCCESS if len(errors) == 0 else ExitCode.VALIDATION_ERROR,
            message="File structure validation completed",
            data=context,
            errors=errors,
            warnings=warnings,
        )

    def test_validation_functions(self) -> OperationResult:
        """Test the validation functions with known good and bad data."""
        errors = []
        warnings = []
        context = {"validation_type": "function_testing"}

        # Test TaskInfo validation with good data
        try:
            good_task = TaskInfo(
                title="Test Task",
                checked=False,
                task_id=1,
                priority="High",
                assignee="TestUser",
                create_date="2025-01-01T12:00:00Z",
                start_date="2025-01-01T12:00:00Z",
                finish_date=None,
                estimated_time="30 minutes",
                description="Test description",
                prerequisites=["None"],
                subtasks={"test_subtask": False},
                raw_block="- [ ] **Test Task**:\n  - **ID**: 1",
            )

            validation = validate_task_data(good_task)
            if not validation.is_valid:
                errors.append(f"Good task failed validation: {validation.errors}")
            else:
                context["good_task_validation"] = "passed"

        except Exception as e:
            errors.append(f"Error testing good task validation: {e}")

        # Test TaskInfo validation with bad data
        try:
            bad_task = TaskInfo(
                title="",  # Invalid: empty title
                checked=False,
                task_id=-1,  # Invalid: negative ID
                priority="Invalid",  # Invalid: not in allowed priorities
                assignee="TestUser",
                create_date="invalid-date",  # Invalid: bad date format
                start_date="2025-01-01T12:00:00Z",
                finish_date=None,
                estimated_time="30 minutes",
                description="Test description",
                prerequisites=["None"],
                subtasks={},
                raw_block="- [ ] **Bad Task**:\n  - **ID**: -1",
            )

            validation = validate_task_data(bad_task)
            if validation.is_valid:
                errors.append("Bad task passed validation when it should have failed")
            else:
                context["bad_task_validation"] = "properly_rejected"
                if len(validation.errors) < 3:  # Should have multiple errors
                    warnings.append(
                        f"Expected more validation errors, got: {len(validation.errors)}"
                    )

        except Exception as e:
            errors.append(f"Error testing bad task validation: {e}")

        # Test prerequisite validation
        try:
            prereq_result = validate_prerequisites()
            context["prerequisite_validation"] = "completed"
            context["prereq_errors"] = len(prereq_result.errors)
            context["prereq_warnings"] = len(prereq_result.warnings)
        except Exception as e:
            errors.append(f"Error testing prerequisite validation: {e}")

        return OperationResult(
            success=len(errors) == 0,
            exit_code=ExitCode.SUCCESS if len(errors) == 0 else ExitCode.SYSTEM_ERROR,
            message="Validation function testing completed",
            data=context,
            errors=errors,
            warnings=warnings,
        )

    def validate_existing_tasks(self) -> OperationResult:
        """Validate the existing tasks file if it exists."""
        errors = []
        warnings = []
        context = {"validation_type": "existing_tasks"}

        if not TASKS_FILE.exists():
            warnings.append(f"Tasks file does not exist: {TASKS_FILE}")
            context["tasks_file_exists"] = False
            return OperationResult(
                success=True,
                exit_code=ExitCode.NO_WORK,
                message="No tasks file to validate",
                data=context,
                errors=errors,
                warnings=warnings,
            )

        context["tasks_file_exists"] = True

        try:
            # Use our validation function
            validation = validate_tasks_file(TASKS_FILE)
            context.update(validation.context)
            errors.extend(validation.errors)
            warnings.extend(validation.warnings)

            if validation.is_valid:
                context["validation_status"] = "passed"

                # Try to load and parse tasks
                try:
                    content, tasks = load_tasks_file(TASKS_FILE, validate=True)
                    context["task_count"] = len(tasks)
                    context["parsing_status"] = "success"

                    # Analyze task distribution
                    priorities = {}
                    assignees = {}
                    completion_status = {"completed": 0, "in_progress": 0}

                    for task in tasks.values():
                        priorities[task.priority] = priorities.get(task.priority, 0) + 1
                        assignee = task.assignee or "unassigned"
                        assignees[assignee] = assignees.get(assignee, 0) + 1

                        if task.checked:
                            completion_status["completed"] += 1
                        else:
                            completion_status["in_progress"] += 1

                    context["priority_distribution"] = priorities
                    context["assignee_distribution"] = assignees
                    context["completion_status"] = completion_status

                except Exception as e:
                    errors.append(f"Error loading tasks file: {e}")
                    context["parsing_status"] = "failed"
            else:
                context["validation_status"] = "failed"

        except Exception as e:
            errors.append(f"Error validating tasks file: {e}")
            context["validation_status"] = "error"

        return OperationResult(
            success=len(errors) == 0,
            exit_code=ExitCode.SUCCESS if len(errors) == 0 else ExitCode.VALIDATION_ERROR,
            message="Existing tasks validation completed",
            data=context,
            errors=errors,
            warnings=warnings,
        )

    def test_git_integration(self) -> OperationResult:
        """Test git integration functions."""
        errors = []
        warnings = []
        context = {"validation_type": "git_integration"}

        try:
            git_info = get_git_info()
            context.update(git_info)

            if git_info["branch"] == "unknown":
                warnings.append("Could not determine git branch")

            if git_info["commit"] == "unknown":
                warnings.append("Could not determine git commit")

            if git_info["user_name"] == "unknown":
                warnings.append("Git user name not configured")

            if git_info["user_email"] == "unknown":
                warnings.append("Git user email not configured")

            if git_info["has_uncommitted"]:
                warnings.append("Working directory has uncommitted changes")

            context["git_functional"] = True

        except Exception as e:
            errors.append(f"Error testing git integration: {e}")
            context["git_functional"] = False

        return OperationResult(
            success=len(errors) == 0,
            exit_code=ExitCode.SUCCESS if len(errors) == 0 else ExitCode.SYSTEM_ERROR,
            message="Git integration testing completed",
            data=context,
            errors=errors,
            warnings=warnings,
        )

    def test_output_formats(self) -> OperationResult:
        """Test JSON and human output formats."""
        errors = []
        warnings = []
        context = {"validation_type": "output_formats"}

        try:
            # Create a test result
            test_result = OperationResult(
                success=True,
                exit_code=ExitCode.SUCCESS,
                message="Test message",
                data={"test": "data"},
                errors=["test error"],
                warnings=["test warning"],
            )

            # Test JSON output (capture but don't print)
            import io
            from contextlib import redirect_stdout

            json_output = io.StringIO()
            with redirect_stdout(json_output):
                output_result(test_result, "json", quiet=True)

            json_content = json_output.getvalue()
            if not json_content.strip():
                errors.append("JSON output is empty")
            else:
                try:
                    import json

                    json.loads(json_content)
                    context["json_format"] = "valid"
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON output: {e}")

            # Test human output
            human_output = io.StringIO()
            with redirect_stdout(human_output):
                output_result(test_result, "human", quiet=True)

            human_content = human_output.getvalue()
            if not human_content.strip():
                warnings.append("Human output is empty")
            else:
                context["human_format"] = "generated"

        except Exception as e:
            errors.append(f"Error testing output formats: {e}")

        return OperationResult(
            success=len(errors) == 0,
            exit_code=ExitCode.SUCCESS if len(errors) == 0 else ExitCode.SYSTEM_ERROR,
            message="Output format testing completed",
            data=context,
            errors=errors,
            warnings=warnings,
        )

    def run_comprehensive_validation(self) -> OperationResult:
        """Run all validation tests and return overall result."""
        if not self.quiet:
            print("🔍 Starting comprehensive automation validation...")
            print(f"📅 Validation time: {get_current_datetime()}")
            print(f"📁 Root directory: {ROOT}")
            print("")

        # Run all validation tests
        validation_tests = [
            ("Module Imports", self.validate_module_imports),
            ("File Structure", self.validate_file_structure),
            ("Validation Functions", self.test_validation_functions),
            ("Existing Tasks", self.validate_existing_tasks),
            ("Git Integration", self.test_git_integration),
            ("Output Formats", self.test_output_formats),
        ]

        for test_name, test_func in validation_tests:
            if not self.quiet:
                print(f"🧪 Running {test_name} validation...")

            try:
                result = test_func()
                self.log_result(result)
            except Exception as e:
                error_result = create_structured_error(
                    f"{test_name} validation failed with exception",
                    ExitCode.SYSTEM_ERROR,
                    [f"Exception: {e}", f"Traceback: {traceback.format_exc()}"],
                    {"test_name": test_name},
                )
                self.log_result(error_result)

            if not self.quiet:
                print("")

        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)

        summary_data = {
            "validation_time": get_current_datetime(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "overall_success": self.overall_success,
        }

        if self.overall_success:
            message = f"✅ All {total_tests} validation tests passed"
            exit_code = ExitCode.SUCCESS
        else:
            message = f"❌ {failed_tests}/{total_tests} validation tests failed"
            exit_code = ExitCode.VALIDATION_ERROR

        if total_warnings > 0:
            message += f" ({total_warnings} warnings)"

        return OperationResult(
            success=self.overall_success,
            exit_code=exit_code,
            message=message,
            data=summary_data,
            errors=[],
            warnings=[],
        )


def main(argv=None):
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Validate task automation system components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s                    # Run all validations with human output
    %(prog)s --format json      # Run validations with JSON output
    %(prog)s --quiet            # Run validations quietly
    %(prog)s --fix-issues       # Attempt to fix detected issues (dry-run)
        """,
    )

    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: %(default)s)",
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output")

    parser.add_argument(
        "--fix-issues",
        action="store_true",
        help="Attempt to fix detected issues (implies --dry-run)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview fixes without applying them"
    )

    args = parser.parse_args(argv)

    # Create validator
    validator = AutomationValidator(quiet=args.quiet, format_type=args.format)

    # Run comprehensive validation
    result = validator.run_comprehensive_validation()

    # Output final result
    if not args.quiet or args.format == "json":
        output_result(result, args.format, args.quiet)

    # Exit with appropriate code
    sys.exit(result.exit_code.value)


if __name__ == "__main__":
    main()
