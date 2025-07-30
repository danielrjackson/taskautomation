#!/usr/bin/env python3
"""
Validation utilities for task automation system.

This module provides comprehensive validation functions for task data,
file operations, and system prerequisites.
"""

from __future__ import annotations

import collections
import datetime
import os
import pathlib
import sys
from typing import Any

from .core_utils import DATETIME_RE, TaskInfo
from .git_helpers import get_git_info, run_git_command
from .task_types import ValidationResult

# Export list for backward compatibility
__all__ = [
    "validate_task_data",
    "validate_tasks_file",
    "verify_operation_safety",
    "validate_prerequisites",
    "extract_assignee",
    "extract_create_date",
    "extract_description",
    "extract_finished_date",
    "extract_task_id",
    "extract_priority",
    "is_valid_task_line",
    "validate_task_format",
    "validate_task_schema",
]

# =============================================================================
# Task Validation Functions
# =============================================================================


def validate_task_data(task: TaskInfo) -> ValidationResult:
    """
    Comprehensively validate a TaskInfo object.

    Args:
        task: TaskInfo object to validate

    Returns:
        ValidationResult with detailed validation information
    """
    errors = []
    warnings = []
    context = {"task_id": task.task_id, "title": task.title}

    # Validate required fields
    if not task.title or not task.title.strip():
        errors.append("Task title is required and cannot be empty")

    if task.task_id <= 0:
        errors.append(f"Task ID must be a positive integer, got: {task.task_id}")

    # Validate priority
    valid_priorities = {"Critical", "High", "Medium", "Low"}
    if task.priority not in valid_priorities:
        errors.append(f"Priority must be one of {valid_priorities}, got: {task.priority}")

    # Validate dates
    for date_field, date_value in [
        ("create_date", task.create_date),
        ("start_date", task.start_date),
        ("finish_date", task.finish_date),
    ]:
        if date_value and not DATETIME_RE.match(date_value):
            errors.append(f"{date_field} must be in ISO8601 format, got: {date_value}")

    # Validate date logic
    if task.create_date and task.start_date:
        try:
            create_dt = datetime.datetime.fromisoformat(task.create_date.rstrip("Z"))
            start_dt = datetime.datetime.fromisoformat(task.start_date.rstrip("Z"))
            if start_dt < create_dt:
                warnings.append("Start date is before create date")
        except ValueError as e:
            errors.append(f"Date parsing error: {e}")

    # Validate completion logic
    if task.checked and not task.finish_date:
        warnings.append("Completed task should have a finish date")

    if not task.checked and task.finish_date:
        warnings.append("Incomplete task should not have a finish date")

    # Validate subtasks
    if task.subtasks:
        all_subtasks_done = all(task.subtasks.values())
        if task.checked and not all_subtasks_done:
            warnings.append("Main task is completed but some subtasks are not")
        elif not task.checked and all_subtasks_done:
            warnings.append("All subtasks completed but main task is not")

    context.update(
        {
            "priority": task.priority,
            "has_subtasks": bool(task.subtasks),
            "subtask_count": len(task.subtasks),
            "completion_status": "completed" if task.checked else "in_progress",
        }
    )

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )


def validate_tasks_file(file_path: pathlib.Path, parse_tasks_func) -> ValidationResult:
    """
    Validate the entire tasks file structure and content.

    Args:
        file_path: Path to tasks file
        parse_tasks_func: Function to parse tasks from file content

    Returns:
        ValidationResult with file-level validation information
    """
    errors: list[str] = []
    warnings: list[str] = []
    context: dict[str, Any] = {"file_path": str(file_path)}

    # Check file existence
    if not file_path.exists():
        errors.append(f"Tasks file does not exist: {file_path}")
        return ValidationResult(False, errors, warnings, context)

    try:
        content = file_path.read_text(encoding="utf-8")
        context["file_size"] = len(content)
        context["line_count"] = len(content.split("\n"))
    except Exception as e:
        errors.append(f"Cannot read tasks file: {e}")
        return ValidationResult(False, errors, warnings, context)

    # Parse and validate tasks
    try:
        tasks = parse_tasks_func(content)
        context["task_count"] = len(tasks)

        # Check for duplicate IDs
        task_ids = [task.task_id for task in tasks.values()]
        duplicates = [tid for tid, count in collections.Counter(task_ids).items() if count > 1]
        if duplicates:
            errors.append(f"Duplicate task IDs found: {duplicates}")

        # Validate each task
        task_errors = []
        task_warnings = []
        for task in tasks.values():
            result = validate_task_data(task)
            task_errors.extend([f"Task {task.task_id}: {err}" for err in result.errors])
            task_warnings.extend([f"Task {task.task_id}: {warn}" for warn in result.warnings])

        errors.extend(task_errors)
        warnings.extend(task_warnings)

    except Exception as e:
        errors.append(f"Error parsing tasks: {e}")

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )


# =============================================================================
# File Operation Validation
# =============================================================================


def verify_operation_safety(
    operation: str, target_files: list[pathlib.Path], dry_run: bool = True
) -> ValidationResult:
    """
    Verify that an operation is safe to perform.

    Args:
        operation: Description of operation
        target_files: Files that will be affected
        dry_run: Whether this is a dry run

    Returns:
        ValidationResult with safety assessment
    """
    errors = []
    warnings = []
    context = {
        "operation": operation,
        "target_files": [str(f) for f in target_files],
        "dry_run": dry_run,
    }

    # Check file permissions
    for file_path in target_files:
        if file_path.exists():
            if not file_path.is_file():
                errors.append(f"Target is not a file: {file_path}")
            elif not os.access(file_path, os.W_OK):
                errors.append(f"No write permission: {file_path}")
        else:
            # Check parent directory permissions
            parent = file_path.parent
            if not parent.exists():
                warnings.append(f"Parent directory will be created: {parent}")
            elif not os.access(parent, os.W_OK):
                errors.append(f"No write permission for parent directory: {parent}")

    # Git repository checks
    git_info = get_git_info()
    if git_info["has_uncommitted"]:
        warnings.append("Working directory has uncommitted changes")

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )


# =============================================================================
# System Prerequisite Validation
# =============================================================================


def validate_prerequisites(root_path: pathlib.Path) -> ValidationResult:
    """
    Validate that all prerequisites for task operations are met.

    Args:
        root_path: Root directory of the project

    Returns:
        ValidationResult with prerequisite check results
    """
    errors: list[str] = []
    warnings: list[str] = []
    context: dict[str, Any] = {}

    # Check Python version
    python_version = sys.version_info
    context["python_version"] = (
        f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version < (3, 8):
        errors.append(f"Python 3.8+ required, found {context['python_version']}")

    # Check required directories
    required_dirs = [root_path / "docs", root_path / "scripts" / "dev"]
    for dir_path in required_dirs:
        if not dir_path.exists():
            errors.append(f"Required directory missing: {dir_path}")

    # Check git availability
    git_available, _, _ = run_git_command(["--version"])
    context["git_available"] = git_available
    if not git_available:
        warnings.append("Git not available - some features may not work")

    # Check if we're in a git repository
    if git_available:
        is_repo, _, _ = run_git_command(["rev-parse", "--git-dir"])
        context["is_git_repo"] = is_repo
        if not is_repo:
            warnings.append("Not in a git repository - some features may not work")

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )


def extract_assignee(task_content: str) -> str:
    """
    Extract assignee information from task content.

    Args:
        task_content: The task content to extract assignee from

    Returns:
        The assignee name or empty string if not found

    Note:
        This is a basic implementation for backward compatibility.
        Looks for patterns like "Assignee: name" or "@username"
    """
    import re

    # Look for "Assignee: name" pattern
    assignee_match = re.search(r"Assignee:\s*([^\n]+)", task_content, re.IGNORECASE)
    if assignee_match:
        return assignee_match.group(1).strip()

    # Look for @username pattern
    at_match = re.search(r"@([a-zA-Z0-9_-]+)", task_content)
    if at_match:
        return at_match.group(1)

    return ""


def extract_create_date(task_content: str) -> str:
    """
    Extract create date information from task content.

    Args:
        task_content: The task content to extract create date from

    Returns:
        The create date in ISO8601 format or empty string if not found

    Note:
        This is a basic implementation for backward compatibility.
        Looks for patterns like "Create Date: YYYY-MM-DD" or similar.
    """
    import re

    # Look for "Create Date: date" pattern
    create_date_match = re.search(r"Create\s+Date:\s*([^\n]+)", task_content, re.IGNORECASE)
    if create_date_match:
        date_str = create_date_match.group(1).strip()
        # Basic validation - should match ISO8601-like format
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

    # Look for "Created: date" pattern
    created_match = re.search(r"Created:\s*([^\n]+)", task_content, re.IGNORECASE)
    if created_match:
        date_str = created_match.group(1).strip()
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

    return ""


def extract_description(task_content: str) -> str:
    """
    Extract task description from task content.

    Args:
        task_content: Raw task content string

    Returns:
        str: Extracted description or empty string if not found
    """
    if not task_content or not isinstance(task_content, str):
        return ""

    # Remove leading/trailing whitespace and return as description
    description = task_content.strip()

    # Remove any markdown formatting for basic description
    # This is a simple implementation - could be enhanced for more complex parsing
    import re

    description = re.sub(r"^#+\s*", "", description)  # Remove heading markers
    description = re.sub(r"\*\*(.*?)\*\*", r"\1", description)  # Remove bold
    description = re.sub(r"\*(.*?)\*", r"\1", description)  # Remove italic

    return description


def extract_finished_date(task_content: str) -> str:
    """
    Extract finished date information from task content.

    Args:
        task_content: The task content to extract finished date from

    Returns:
        The finished date in ISO8601 format or empty string if not found

    Note:
        This is a basic implementation for backward compatibility.
        Looks for patterns like "Finished Date: YYYY-MM-DD" or similar.
    """
    import re

    # Look for "Finished Date: date" pattern
    finished_date_match = re.search(r"Finished\s+Date:\s*([^\n]+)", task_content, re.IGNORECASE)
    if finished_date_match:
        date_str = finished_date_match.group(1).strip()
        # Basic validation - should match ISO8601-like format
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

    # Look for "Completed: date" pattern
    completed_match = re.search(r"Completed:\s*([^\n]+)", task_content, re.IGNORECASE)
    if completed_match:
        date_str = completed_match.group(1).strip()
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

    # Look for "Finished: date" pattern
    finished_match = re.search(r"Finished:\s*([^\n]+)", task_content, re.IGNORECASE)
    if finished_match:
        date_str = finished_match.group(1).strip()
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

    return ""


def extract_task_id(task_content: str) -> str:
    """
    Extract task ID information from task content.

    Args:
        task_content: The task content to extract task ID from

    Returns:
        The task ID or empty string if not found

    Note:
        This is a basic implementation for backward compatibility.
        Looks for patterns like "ID: T-123" or similar.
    """
    import re

    # Look for "ID: identifier" pattern
    id_match = re.search(r"ID:\s*([^\n\s]+)", task_content, re.IGNORECASE)
    if id_match:
        return id_match.group(1).strip()

    # Look for "Task ID: identifier" pattern
    task_id_match = re.search(r"Task\s+ID:\s*([^\n\s]+)", task_content, re.IGNORECASE)
    if task_id_match:
        return task_id_match.group(1).strip()

    # Look for bracketed ID like [T-123]
    bracket_match = re.search(r"\[([A-Z]+-\d+)\]", task_content)
    if bracket_match:
        return bracket_match.group(1)

    # Look for T-### pattern
    t_pattern_match = re.search(r"(T-\d+)", task_content)
    if t_pattern_match:
        return t_pattern_match.group(1)

    return ""


def is_valid_task_line(line: str) -> bool:
    """
    Check if a line represents a valid task format.

    Args:
        line: The line to validate

    Returns:
        bool: True if the line is a valid task line, False otherwise

    Note:
        This is a basic implementation for backward compatibility.
        Checks for common task line patterns.
    """
    import re

    if not line or not isinstance(line, str):
        return False

    line = line.strip()

    # Check for markdown checklist format
    if re.match(r"^[\s]*[-*+]\s*\[[\sx]\]", line):
        return True

    # Check for numbered task format
    if re.match(r"^[\s]*\d+\.\s+", line):
        return True

    # Check for basic task indicators
    task_indicators = ["TODO:", "TASK:", "Action:", "Do:", "- [ ]", "- [x]"]
    for indicator in task_indicators:
        if indicator.lower() in line.lower():
            return True

    # Check for task ID patterns
    if re.search(r"(T-\d+|ID:\s*\w+)", line):
        return True

    return False


def extract_priority(task_content: str) -> str:
    """
    Extract priority information from task content.

    Args:
        task_content: The task content to extract priority from

    Returns:
        The priority level or empty string if not found

    Note:
        This is a basic implementation for backward compatibility.
        Looks for patterns like "Priority: High" or similar.
    """
    import re

    # Look for "Priority: level" pattern
    priority_match = re.search(r"Priority:\s*([^\n]+)", task_content, re.IGNORECASE)
    if priority_match:
        priority_str = priority_match.group(1).strip()
        # Normalize common priority values
        priority_lower = priority_str.lower()
        if priority_lower in ["high", "medium", "low", "critical", "urgent"]:
            return priority_str.title()  # Return with proper capitalization

    # Look for bracketed priority like [HIGH], [MEDIUM], [LOW]
    bracket_match = re.search(r"\[([A-Z]+)\]", task_content)
    if bracket_match:
        priority_str = bracket_match.group(1)
        priority_lower = priority_str.lower()
        if priority_lower in ["high", "medium", "low", "critical", "urgent"]:
            return priority_str.title()

    return ""


def validate_task_format(task_line: str) -> bool:
    """
    Validate that a task line follows the correct format.

    Args:
        task_line: The task line to validate

    Returns:
        bool: True if the task line is properly formatted, False otherwise

    Note:
        This is a basic implementation for backward compatibility.
        Validates common task formats including markdown checkboxes,
        numbered lists, and TODO/TASK indicators.
    """
    if not task_line or not isinstance(task_line, str):
        return False

    # Use the existing is_valid_task_line function for validation
    return is_valid_task_line(task_line)


def validate_task_schema(task_data: dict) -> ValidationResult:
    """
    Validate that task data conforms to the expected schema.

    Args:
        task_data: Dictionary containing task data to validate

    Returns:
        ValidationResult: Result of schema validation

    Note:
        This is a basic implementation for backward compatibility.
        Validates common task schema requirements.
    """
    errors = []
    warnings = []
    context = {"validation_type": "schema", "task_data_keys": list(task_data.keys())}

    if not isinstance(task_data, dict):
        errors.append("Task data must be a dictionary")
        return ValidationResult(False, errors, warnings, context)

    # Check for required fields
    required_fields = ["title", "task_id"]
    for field in required_fields:
        if field not in task_data:
            errors.append(f"Required field missing: {field}")
        elif not task_data[field]:
            errors.append(f"Required field cannot be empty: {field}")

    # Validate task_id is numeric if present
    if "task_id" in task_data:
        try:
            task_id = int(task_data["task_id"])
            if task_id <= 0:
                errors.append("Task ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Task ID must be numeric")

    # Validate priority if present
    if "priority" in task_data:
        valid_priorities = {"Critical", "High", "Medium", "Low"}
        if task_data["priority"] not in valid_priorities:
            errors.append(f"Priority must be one of {valid_priorities}")

    # Validate status if present
    if "status" in task_data:
        valid_statuses = {"todo", "in_progress", "done", "cancelled"}
        if task_data["status"] not in valid_statuses:
            warnings.append(f"Status should be one of {valid_statuses}")

    # Validate date fields if present
    date_fields = ["create_date", "start_date", "finish_date"]
    for field in date_fields:
        if field in task_data and task_data[field]:
            if not DATETIME_RE.match(task_data[field]):
                errors.append(f"{field} must be in ISO8601 format")

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )
