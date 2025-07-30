#!/usr/bin/env python3
"""
Comprehensive tests for validate_automation.py script.

Tests the configurable path system and all functionality of the automation validator.
"""

import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from taskautomation.task_utils import ExitCode, OperationResult
from taskautomation.validate_automation import (
    AutomationValidator,
    get_paths,
    main,
)


class TestValidateAutomation(unittest.TestCase):
    """Test cases for validate_automation script."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.test_root = pathlib.Path(self.test_dir)

        # Set up test directory structure
        self.setup_test_directory()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def setup_test_directory(self):
        """Set up the test directory structure."""
        # Create necessary directories
        (self.test_root / "docs").mkdir(parents=True)
        (self.test_root / "docs" / "planning").mkdir(parents=True)
        (self.test_root / "src" / "taskautomation").mkdir(parents=True)

        # Copy test data files
        test_data_dir = pathlib.Path(__file__).parent / "data"

        # Copy TASKS.md
        if (test_data_dir / "sample_tasks.md").exists():
            shutil.copy2(test_data_dir / "sample_tasks.md", self.test_root / "docs" / "TASKS.md")
        else:
            # Create a basic tasks file if test data doesn't exist
            tasks_content = """# Test Tasks

## Current Tasks

- [ ] **Test Task 1**:
  - **ID**: 1
  - **Priority**: High
  - **Assignee**: TestUser
  - **Create Date**: 2025-01-01T12:00:00Z
  - **Description**: A test task

- [x] **Completed Task**:
  - **ID**: 2
  - **Priority**: Medium
  - **Assignee**: TestUser
  - **Create Date**: 2025-01-01T10:00:00Z
  - **Finished Date**: 2025-01-01T11:00:00Z
  - **Description**: A completed test task
"""
            (self.test_root / "docs" / "TASKS.md").write_text(tasks_content)

        # Create required script files
        self.create_required_scripts()

    def create_required_scripts(self):
        """Create the required script files for validation."""
        scripts_dir = self.test_root / "src" / "taskautomation"

        # Create dummy script files that validation expects
        required_scripts = [
            "task_utils.py",
            "create_change_entry.py",
            "run_tests.py",
        ]

        for script in required_scripts:
            script_path = scripts_dir / script
            script_content = f'''#!/usr/bin/env python3
"""
Test {script} for validation testing.
"""

def main():
    """Main function for testing."""
    return "Test {script} executed"

if __name__ == "__main__":
    main()
'''
            script_path.write_text(script_content)

    def test_get_paths_default(self):
        """Test get_paths function with default root."""
        paths = get_paths()

        # Should return dictionary with required keys
        required_keys = ["ROOT", "TASKS_FILE", "SRC_DIR", "DOCS_DIR", "PLANNING_DIR"]
        for key in required_keys:
            self.assertIn(key, paths)
            self.assertIsInstance(paths[key], pathlib.Path)

    def test_get_paths_override(self):
        """Test get_paths function with root override."""
        paths = get_paths(self.test_root)

        # Should use overridden root
        self.assertEqual(paths["ROOT"], self.test_root)
        self.assertEqual(paths["TASKS_FILE"], self.test_root / "docs" / "TASKS.md")
        self.assertEqual(paths["SRC_DIR"], self.test_root / "src" / "taskautomation")
        self.assertEqual(paths["DOCS_DIR"], self.test_root / "docs")
        self.assertEqual(paths["PLANNING_DIR"], self.test_root / "docs" / "planning")

    def test_automation_validator_initialization(self):
        """Test AutomationValidator initialization with configurable paths."""
        validator = AutomationValidator(root_override=self.test_root)

        # Should initialize properly
        self.assertIsNotNone(validator)
        self.assertFalse(validator.quiet)
        self.assertEqual(validator.format_type, "human")
        self.assertTrue(validator.overall_success)
        self.assertEqual(len(validator.results), 0)
        self.assertEqual(validator.paths["ROOT"], self.test_root)

    def test_automation_validator_initialization_options(self):
        """Test AutomationValidator initialization with options."""
        validator = AutomationValidator(
            quiet=True, format_type="json", root_override=self.test_root
        )

        # Should initialize with specified options
        self.assertTrue(validator.quiet)
        self.assertEqual(validator.format_type, "json")
        self.assertEqual(validator.paths["ROOT"], self.test_root)

    def test_validate_module_imports(self):
        """Test validate_module_imports method."""
        validator = AutomationValidator(root_override=self.test_root)

        result = validator.validate_module_imports()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_validate_file_structure(self):
        """Test validate_file_structure method."""
        validator = AutomationValidator(root_override=self.test_root)

        result = validator.validate_file_structure()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_test_validation_functions(self):
        """Test test_validation_functions method."""
        validator = AutomationValidator(root_override=self.test_root)

        result = validator.test_validation_functions()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_validate_existing_tasks(self):
        """Test validate_existing_tasks method."""
        validator = AutomationValidator(root_override=self.test_root)

        result = validator.validate_existing_tasks()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_test_git_integration(self):
        """Test test_git_integration method."""
        validator = AutomationValidator(root_override=self.test_root)

        result = validator.test_git_integration()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_test_output_formats(self):
        """Test test_output_formats method."""
        validator = AutomationValidator(root_override=self.test_root)

        result = validator.test_output_formats()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_get_available_tests(self):
        """Test get_available_tests method."""
        validator = AutomationValidator(root_override=self.test_root)

        tests = validator.get_available_tests()

        # Should return dictionary of test functions
        self.assertIsInstance(tests, dict)
        expected_tests = ["imports", "structure", "functions", "tasks", "git", "output"]
        for test_name in expected_tests:
            self.assertIn(test_name, tests)
            self.assertTrue(callable(tests[test_name]))

    def test_list_available_tests_human(self):
        """Test list_available_tests method with human format."""
        validator = AutomationValidator(format_type="human", root_override=self.test_root)

        with patch("sys.stdout"):
            validator.list_available_tests()

        # Should execute without error
        self.assertTrue(True)

    def test_list_available_tests_json(self):
        """Test list_available_tests method with JSON format."""
        validator = AutomationValidator(format_type="json", root_override=self.test_root)

        with patch("sys.stdout"):
            validator.list_available_tests()

        # Should execute without error
        self.assertTrue(True)

    def test_run_selective_validation(self):
        """Test run_selective_validation method."""
        validator = AutomationValidator(quiet=True, root_override=self.test_root)

        result = validator.run_selective_validation(["imports", "structure"])

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_run_selective_validation_invalid_tests(self):
        """Test run_selective_validation method with invalid test names."""
        validator = AutomationValidator(quiet=True, root_override=self.test_root)

        result = validator.run_selective_validation(["invalid_test", "another_invalid"])

        # Should return error result
        self.assertIsInstance(result, OperationResult)
        self.assertFalse(result.success)

    def test_run_comprehensive_validation(self):
        """Test run_comprehensive_validation method."""
        validator = AutomationValidator(quiet=True, root_override=self.test_root)

        result = validator.run_comprehensive_validation()

        # Should return OperationResult
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "exit_code"))
        self.assertTrue(hasattr(result, "message"))

    def test_main_default_behavior(self):
        """Test main function with default behavior."""
        with patch("sys.stdout"):
            try:
                result = main([], root_override=self.test_root)
            except SystemExit as e:
                # main() calls sys.exit(), capture the exit code
                self.assertIsInstance(e.code, int)

    def test_main_with_format_json(self):
        """Test main function with JSON format."""
        with patch("sys.stdout"):
            try:
                result = main(["--format", "json"], root_override=self.test_root)
            except SystemExit as e:
                self.assertIsInstance(e.code, int)

    def test_main_with_quiet_flag(self):
        """Test main function with quiet flag."""
        with patch("sys.stdout"):
            try:
                result = main(["--quiet"], root_override=self.test_root)
            except SystemExit as e:
                self.assertIsInstance(e.code, int)

    def test_main_with_selective_tests(self):
        """Test main function with selective tests."""
        with patch("sys.stdout"):
            try:
                result = main(["--tests", "imports,structure"], root_override=self.test_root)
            except SystemExit as e:
                self.assertIsInstance(e.code, int)

    def test_main_with_list_tests(self):
        """Test main function with list-tests option."""
        with patch("sys.stdout"):
            try:
                result = main(["--list-tests"], root_override=self.test_root)
            except SystemExit as e:
                # Should exit with 0 for successful listing
                self.assertEqual(e.code, 0)

    def test_main_with_fix_issues(self):
        """Test main function with fix-issues flag."""
        with patch("sys.stdout"):
            try:
                result = main(["--fix-issues"], root_override=self.test_root)
            except SystemExit as e:
                self.assertIsInstance(e.code, int)

    def test_main_with_dry_run(self):
        """Test main function with dry-run flag."""
        with patch("sys.stdout"):
            try:
                result = main(["--dry-run"], root_override=self.test_root)
            except SystemExit as e:
                self.assertIsInstance(e.code, int)

    def test_isolated_test_environment(self):
        """Test that the test environment is properly isolated."""
        # Test directory should exist
        self.assertTrue(self.test_root.exists())

        # Required directories should exist
        self.assertTrue((self.test_root / "docs").exists())
        self.assertTrue((self.test_root / "src" / "taskautomation").exists())
        self.assertTrue((self.test_root / "docs" / "planning").exists())

        # Required files should exist
        self.assertTrue((self.test_root / "docs" / "TASKS.md").exists())

    def test_validation_with_missing_files(self):
        """Test validation behavior when required files are missing."""
        # Remove a required file
        tasks_file = self.test_root / "docs" / "TASKS.md"
        if tasks_file.exists():
            tasks_file.unlink()

        validator = AutomationValidator(quiet=True, root_override=self.test_root)
        result = validator.validate_existing_tasks()

        # Should handle missing file gracefully
        self.assertIsInstance(result, OperationResult)

    def test_validation_with_missing_directories(self):
        """Test validation behavior when required directories are missing."""
        # Remove a required directory
        planning_dir = self.test_root / "docs" / "planning"
        if planning_dir.exists():
            shutil.rmtree(planning_dir)

        validator = AutomationValidator(quiet=True, root_override=self.test_root)
        result = validator.validate_file_structure()

        # Should detect missing directory
        self.assertIsInstance(result, OperationResult)

    def test_log_result_functionality(self):
        """Test log_result method functionality."""
        validator = AutomationValidator(quiet=True, root_override=self.test_root)

        # Create a test result
        test_result = OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="Test result",
            data={},
            errors=[],
            warnings=[],
        )

        # Log the result
        validator.log_result(test_result)

        # Should be added to results
        self.assertEqual(len(validator.results), 1)
        self.assertEqual(validator.results[0], test_result)
        self.assertTrue(validator.overall_success)

    def test_log_result_with_failure(self):
        """Test log_result method with failure result."""
        validator = AutomationValidator(quiet=True, root_override=self.test_root)

        # Create a failure result
        failure_result = OperationResult(
            success=False,
            exit_code=ExitCode.VALIDATION_ERROR,
            message="Test failure",
            data={},
            errors=["Test error"],
            warnings=[],
        )

        # Log the result
        validator.log_result(failure_result)

        # Should update overall success
        self.assertEqual(len(validator.results), 1)
        self.assertFalse(validator.overall_success)

    def test_help_option(self):
        """Test help option functionality."""
        with patch("sys.stdout"):
            try:
                result = main(["--help"], root_override=self.test_root)
            except SystemExit as e:
                # argparse calls sys.exit() on --help
                self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
