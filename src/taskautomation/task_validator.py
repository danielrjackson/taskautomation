#!/usr/bin/env python3
"""
YAML-based task validation functionality for the automation system.

This module provides comprehensive validation functions for YAML task files,
task objects, and automation workflows with detailed error reporting using
the schema validation system.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .task_schema import Task, TaskList, TaskStatus, ValidationError
from .task_types import ExitCode, OperationResult, ValidationResult, create_structured_error


def validate_task_object(task: Task) -> ValidationResult:
    """
    Validate a Task object for completeness and logical consistency.

    Parameters
    ----------
    task : Task
        Task object to validate

    Returns
    -------
    ValidationResult
        Validation result with success status and any errors
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        # Basic field validation is handled by the Task constructor
        # But we can add logical consistency checks here

        # Check date consistency
        if task.start_date and task.finish_date:
            if task.start_date > task.finish_date:
                errors.append(f"Task {task.id}: Start date cannot be after finish date")

        # Check completion consistency with subtasks
        if task.status == TaskStatus.COMPLETED and task.subtasks:
            uncompleted_subtasks = [st.name for st in task.subtasks if not st.completed and st.name]
            if uncompleted_subtasks:
                subtask_list = ", ".join(uncompleted_subtasks)
                warnings.append(
                    f"Task {task.id} is marked complete but has uncompleted subtasks: {subtask_list}"
                )

        # Check if task has both start date and in_progress status consistency
        if task.status == TaskStatus.IN_PROGRESS and not task.start_date:
            warnings.append(f"Task {task.id} is in progress but has no start date")

        # Check if completed task has finish date
        if task.status == TaskStatus.COMPLETED and not task.finish_date:
            warnings.append(f"Task {task.id} is completed but has no finish date")

        # Validate estimated time format if provided
        if task.estimated_time and not _is_valid_time_estimate(task.estimated_time):
            warnings.append(
                f"Task {task.id}: Estimated time should be in format like '30 minutes', '2 hours', '1 day'"
            )

    except Exception as e:
        errors.append(f"Unexpected error validating task {task.id}: {e}")

    success = len(errors) == 0
    return ValidationResult(
        is_valid=success,
        errors=errors,
        warnings=warnings,
        context={"exit_code": ExitCode.SUCCESS if success else ExitCode.VALIDATION_ERROR},
    )


def validate_task_list(task_list: TaskList) -> ValidationResult:
    """
    Validate a TaskList object for consistency and dependencies.

    Parameters
    ----------
    task_list : TaskList
        TaskList object to validate

    Returns
    -------
    ValidationResult
        Validation result with success status and any errors
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        all_tasks = task_list.get_all_tasks()

        # Check for duplicate task IDs
        _check_duplicate_task_ids(all_tasks, errors)

        # Check prerequisites exist
        _check_prerequisites_exist(all_tasks, errors)

        # Check for circular dependencies
        _check_circular_dependencies(all_tasks, errors)

        # Check completion consistency
        _check_completion_consistency(all_tasks, warnings)

        # Validate individual tasks
        for task in all_tasks:
            task_result = validate_task_object(task)
            errors.extend(task_result.errors)
            warnings.extend(task_result.warnings)

    except Exception as e:
        errors.append(f"Unexpected error validating task list: {e}")

    success = len(errors) == 0
    return ValidationResult(
        is_valid=success,
        errors=errors,
        warnings=warnings,
        context={"exit_code": ExitCode.SUCCESS if success else ExitCode.VALIDATION_ERROR},
    )


def validate_yaml_file(file_path: str | Path) -> ValidationResult:
    """
    Validate a YAML task file exists, is readable, and has valid structure.

    Parameters
    ----------
    file_path : str | Path
        Path to the YAML task file

    Returns
    -------
    ValidationResult
        Validation result with success status and any errors
    """
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(file_path)

    # Check file existence
    if not path.exists():
        errors.append(f"Task file not found: {file_path}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            context={"exit_code": ExitCode.SYSTEM_ERROR},
        )

    # Check file is readable
    try:
        with path.open("r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError:
        errors.append(f"Permission denied reading file: {file_path}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            context={"exit_code": ExitCode.SYSTEM_ERROR},
        )
    except UnicodeDecodeError:
        errors.append(f"File encoding error - file must be UTF-8: {file_path}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            context={"exit_code": ExitCode.SYSTEM_ERROR},
        )

    # Check if file is empty
    if not content.strip():
        warnings.append("Task file is empty")
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            context={"exit_code": ExitCode.SUCCESS},
        )

    # Try to parse YAML
    try:
        data = yaml.safe_load(content)
        if data is None:
            warnings.append("YAML file contains no data")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                context={"exit_code": ExitCode.SUCCESS},
            )
    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error: {e}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            context={"exit_code": ExitCode.VALIDATION_ERROR},
        )

    # Try to validate with schema
    try:
        task_list = TaskList(data)
        # If we got here, basic structure is valid

        # Run full validation on the TaskList
        list_result = validate_task_list(task_list)
        errors.extend(list_result.errors)
        warnings.extend(list_result.warnings)

    except ValidationError as e:
        errors.append(f"Schema validation error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error validating YAML structure: {e}")

    success = len(errors) == 0
    return ValidationResult(
        is_valid=success,
        errors=errors,
        warnings=warnings,
        context={"exit_code": ExitCode.SUCCESS if success else ExitCode.VALIDATION_ERROR},
    )


def validate_yaml_content(content: str) -> OperationResult:
    """
    Validate YAML content string for syntax and schema compliance.

    Parameters
    ----------
    content : str
        YAML content to validate

    Returns
    -------
    OperationResult
        Validation result with detailed information
    """
    try:
        # Parse YAML
        data = yaml.safe_load(content)

        if data is None:
            return OperationResult(
                success=True,
                exit_code=ExitCode.SUCCESS,
                message="Empty YAML content is valid",
                data={"structure": "empty"},
                errors=[],
                warnings=["Content is empty"],
            )

        # Validate with schema
        task_list = TaskList(data)
        list_result = validate_task_list(task_list)

        return OperationResult(
            success=list_result.is_valid,
            exit_code=ExitCode.SUCCESS if list_result.is_valid else ExitCode.VALIDATION_ERROR,
            message="YAML validation complete",
            data={
                "structure": "valid" if list_result.is_valid else "invalid",
                "task_count": len(task_list.get_all_tasks()),
                "archive_count": len(task_list.archive),
            },
            errors=list_result.errors,
            warnings=list_result.warnings,
        )

    except yaml.YAMLError as e:
        return create_structured_error(
            "YAML syntax error", ExitCode.VALIDATION_ERROR, errors=[f"YAML parsing failed: {e}"]
        )
    except ValidationError as e:
        return create_structured_error(
            "Schema validation failed", ExitCode.VALIDATION_ERROR, errors=[str(e)]
        )
    except Exception as e:
        return create_structured_error(
            "Unexpected validation error", ExitCode.SYSTEM_ERROR, errors=[str(e)]
        )


def validate_automation_environment() -> ValidationResult:
    """
    Validate the automation environment is properly set up for YAML-based tasks.

    Returns
    -------
    ValidationResult
        Validation result with success status and any errors
    """
    errors = []
    warnings = []

    # Check required directories exist
    required_dirs = ["scripts/dev", "docs"]
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            errors.append(f"Required directory missing: {dir_path}")

    # Check required files exist for YAML system
    required_files = [
        "scripts/dev/task_schema.py",
        "scripts/dev/task_types.py",
        "scripts/dev/task_parser.py",
    ]
    for file_path in required_files:
        if not os.path.exists(file_path):
            errors.append(f"Required file missing: {file_path}")

    # Check git repository
    if not os.path.exists(".git"):
        warnings.append("Not in a git repository - some features may not work")

    # Check Python environment and required packages
    try:
        import sys

        python_version = f"Python {sys.version_info.major}.{sys.version_info.minor}"

        # Check minimum Python version for the features we use
        if sys.version_info < (3, 8):
            errors.append(f"{python_version} detected - Python 3.8+ required for type hints")
        else:
            warnings.append(f"{python_version} detected - compatible version")

    except Exception as e:
        warnings.append(f"Could not check Python version: {e}")

    # Check required packages are available
    required_packages = [("yaml", "PyYAML"), ("pydantic", "pydantic")]

    for package_name, pip_name in required_packages:
        try:
            __import__(package_name)
        except ImportError:
            errors.append(f"Required package missing: {pip_name}")

    success = len(errors) == 0
    return ValidationResult(
        is_valid=success,
        errors=errors,
        warnings=warnings,
        context={"exit_code": ExitCode.SUCCESS if success else ExitCode.VALIDATION_ERROR},
    )


def _check_duplicate_task_ids(tasks: list[Task], errors: list[str]) -> None:
    """Check for duplicate task IDs."""
    task_ids: dict[int, str] = {}
    for task in tasks:
        # Task validation ensures id and title are never None for valid tasks
        task_id = task.id
        task_title = task.title
        if task_id is not None and task_title is not None:
            if task_id in task_ids:
                errors.append(
                    f"Duplicate task ID {task_id}: '{task_title}' and '{task_ids[task_id]}'"
                )
            else:
                task_ids[task_id] = task_title


def _check_prerequisites_exist(tasks: list[Task], errors: list[str]) -> None:
    """Check that all prerequisites exist."""
    all_task_titles = {task.title for task in tasks if task.title is not None}
    for task in tasks:
        if task.title is not None:
            for prereq in task.prerequisites:
                if prereq not in all_task_titles:
                    errors.append(f"Task '{task.title}' has unknown prerequisite: '{prereq}'")


def _check_circular_dependencies(tasks: list[Task], errors: list[str]) -> None:
    """Check for circular dependencies."""
    task_dict = {task.title: task for task in tasks if task.title is not None}

    for task in tasks:
        if task.title is not None and _has_circular_dependency(
            task.title, task, task_dict, visited=set()
        ):
            errors.append(f"Circular dependency detected involving task: '{task.title}'")


def _check_completion_consistency(tasks: list[Task], warnings: list[str]) -> None:
    """Check completion consistency with prerequisites."""
    task_dict = {task.title: task for task in tasks if task.title is not None}

    for task in tasks:
        if task.status == TaskStatus.COMPLETED and task.title is not None:
            # Check if all prerequisites are complete
            incomplete_prereqs = []
            for prereq in task.prerequisites:
                if prereq in task_dict and task_dict[prereq].status != TaskStatus.COMPLETED:
                    incomplete_prereqs.append(prereq)

            if incomplete_prereqs:
                prereq_list = ", ".join(incomplete_prereqs)
                warnings.append(
                    f"Task '{task.title}' is complete but has incomplete prerequisites: {prereq_list}"
                )


def _has_circular_dependency(
    current_task: str, task: Task, all_tasks: dict[str, Task], visited: set[str]
) -> bool:
    """Check for circular dependencies in task prerequisites."""
    if current_task in visited:
        return True

    visited = visited | {current_task}

    for prereq in task.prerequisites:
        if prereq in all_tasks:
            if _has_circular_dependency(prereq, all_tasks[prereq], all_tasks, visited):
                return True

    return False


def _is_valid_time_estimate(time_str: str) -> bool:
    """Check if time estimate string is in a reasonable format."""
    import re

    time_patterns = [
        r"\d+\s*minutes?",
        r"\d+\s*hours?",
        r"\d+\s*days?",
        r"\d+\s*weeks?",
        r"\d+[hm]",  # 2h, 30m
        r"\d+:\d+",  # 2:30 (hours:minutes)
    ]

    for pattern in time_patterns:
        if re.match(pattern, time_str.lower().strip()):
            return True
    return False


def create_validation_summary(results: list[ValidationResult]) -> dict[str, Any]:
    """
    Create a summary of multiple validation results.

    Parameters
    ----------
    results : list[ValidationResult]
        List of validation results to summarize

    Returns
    -------
    dict[str, Any]
        Summary with counts and aggregated messages
    """
    total_errors = []
    total_warnings = []
    success_count = 0

    for result in results:
        if result.is_valid:
            success_count += 1
        total_errors.extend(result.errors)
        total_warnings.extend(result.warnings)

    return {
        "total_validations": len(results),
        "successful_validations": success_count,
        "failed_validations": len(results) - success_count,
        "total_errors": len(total_errors),
        "total_warnings": len(total_warnings),
        "errors": total_errors,
        "warnings": total_warnings,
        "overall_success": len(total_errors) == 0,
    }


def validate_schema_compatibility(data: dict[str, Any]) -> ValidationResult:
    """
    Validate that data structure is compatible with current schema version.

    Parameters
    ----------
    data : dict[str, Any]
        Data structure to validate

    Returns
    -------
    ValidationResult
        Validation result indicating schema compatibility
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        # Check for required top-level keys
        expected_keys = {"critical", "high", "medium", "low", "archive"}
        missing_keys = expected_keys - set(data.keys())

        if missing_keys:
            warnings.append(f"Missing priority sections: {', '.join(sorted(missing_keys))}")

        # Check metadata if present
        if "metadata" in data:
            metadata = data["metadata"]
            if not isinstance(metadata, dict):
                errors.append("Metadata must be a dictionary")
            else:
                # Check for version info
                if "version" not in metadata:
                    warnings.append("No version information in metadata")

        # Try to create TaskList to verify structure
        TaskList(data)

    except ValidationError as e:
        errors.append(f"Schema compatibility error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error checking schema compatibility: {e}")

    success = len(errors) == 0
    return ValidationResult(
        is_valid=success,
        errors=errors,
        warnings=warnings,
        context={"exit_code": ExitCode.SUCCESS if success else ExitCode.VALIDATION_ERROR},
    )
