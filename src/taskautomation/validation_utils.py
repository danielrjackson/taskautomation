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
