#!/usr/bin/env python3
"""
Core data structures for task automation system.

This module defines the fundamental data types used throughout the
task automation system, including enums, named tuples, and type aliases.
Updated to work with YAML-based task storage and schema validation.
"""

from __future__ import annotations

import enum
from typing import Any, NamedTuple

# Import YAML schema components
from .task_schema import Priority, Subtask, Task, TaskList, TaskStatus


class ExitCode(enum.IntEnum):

    """Standardized exit codes for all automation scripts."""

    SUCCESS = 0  # Operation completed successfully
    NO_WORK = 1  # No work needed (e.g., all tasks completed)
    VALIDATION_ERROR = 2  # Validation failed (bad data, missing requirements)
    SYSTEM_ERROR = 3  # System error (file I/O, git, etc.)
    USER_ABORT = 4  # User aborted operation


class ValidationResult(NamedTuple):

    """Result of validation operations."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    context: dict[str, Any]


class OperationResult(NamedTuple):

    """Result of task operations with structured data."""

    success: bool
    exit_code: ExitCode
    message: str
    data: dict[str, Any]
    errors: list[str]
    warnings: list[str]


class TaskOperationResult(NamedTuple):

    """Result of task-specific operations with YAML schema data."""

    success: bool
    exit_code: ExitCode
    message: str
    task_list: TaskList | None
    modified_tasks: list[Task]
    errors: list[str]
    warnings: list[str]


# Type aliases for cleaner code
TaskId = int
TaskDict = dict[str, Any]
SubtaskDict = dict[str, Any]
TaskListDict = dict[str, Any]


def create_structured_error(
    message: str,
    exit_code: ExitCode,
    errors: list[str] | None = None,
    context: dict[str, Any] | None = None,
) -> OperationResult:
    """
    Create a structured error result.

    Parameters
    ----------
    message : str
        Main error message
    exit_code : ExitCode
        Appropriate exit code
    errors : list[str] | None, optional
        List of detailed errors, by default None
    context : dict[str, Any] | None, optional
        Additional context data, by default None

    Returns
    -------
    OperationResult
        OperationResult with error information
    """
    return OperationResult(
        success=False,
        exit_code=exit_code,
        message=message,
        data=context or {},
        errors=errors or [],
        warnings=[],
    )


def create_task_operation_error(
    message: str,
    exit_code: ExitCode,
    errors: list[str] | None = None,
    task_list: TaskList | None = None,
) -> TaskOperationResult:
    """
    Create a structured error result for task operations.

    Parameters
    ----------
    message : str
        Main error message
    exit_code : ExitCode
        Appropriate exit code
    errors : list[str] | None, optional
        List of detailed errors, by default None
    task_list : TaskList | None, optional
        Current task list state, by default None

    Returns
    -------
    TaskOperationResult
        TaskOperationResult with error information
    """
    return TaskOperationResult(
        success=False,
        exit_code=exit_code,
        message=message,
        task_list=task_list,
        modified_tasks=[],
        errors=errors or [],
        warnings=[],
    )


def create_validation_result(
    is_valid: bool,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    context: dict[str, Any] | None = None,
) -> ValidationResult:
    """
    Create a validation result with standardized structure.

    Parameters
    ----------
    is_valid : bool
        Whether validation passed
    errors : list[str] | None, optional
        List of validation errors, by default None
    warnings : list[str] | None, optional
        List of validation warnings, by default None
    context : dict[str, Any] | None, optional
        Additional validation context, by default None

    Returns
    -------
    ValidationResult
        ValidationResult with validation information
    """
    return ValidationResult(
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
        context=context or {},
    )


def task_to_dict(task: Task) -> TaskDict:
    """
    Convert a Task object to dictionary representation.

    Parameters
    ----------
    task : Task
        Task object to convert

    Returns
    -------
    TaskDict
        Dictionary representation of the task
    """
    return task.to_dict()


def subtask_to_dict(subtask: Subtask) -> SubtaskDict:
    """
    Convert a Subtask object to dictionary representation.

    Parameters
    ----------
    subtask : Subtask
        Subtask object to convert

    Returns
    -------
    SubtaskDict
        Dictionary representation of the subtask
    """
    return subtask.to_dict()


def task_list_to_dict(task_list: TaskList) -> TaskListDict:
    """
    Convert a TaskList object to dictionary representation.

    Parameters
    ----------
    task_list : TaskList
        TaskList object to convert

    Returns
    -------
    TaskListDict
        Dictionary representation of the task list
    """
    return task_list.to_dict()


def get_task_summary(task: Task) -> str:
    """
    Get a concise summary string for a task.

    Parameters
    ----------
    task : Task
        Task to summarize

    Returns
    -------
    str
        Summary string in format: "ID: title [status] (priority)"
    """
    return f"{task.id}: {task.title} [{task.status.value}] ({task.priority.value})"


def get_task_list_summary(task_list: TaskList) -> dict[str, Any]:
    """
    Get summary statistics for a task list.

    Parameters
    ----------
    task_list : TaskList
        TaskList to summarize

    Returns
    -------
    dict[str, Any]
        Summary statistics with counts by status and priority
    """
    all_tasks = task_list.get_all_tasks()

    # Count by status
    status_counts: dict[str, int] = {}
    for status in TaskStatus:
        status_counts[status.value] = sum(1 for task in all_tasks if task.status == status)

    # Count by priority
    priority_counts: dict[str, int] = {}
    for priority in Priority:
        priority_counts[priority.value] = sum(1 for task in all_tasks if task.priority == priority)

    return {
        "total_tasks": len(all_tasks),
        "archived_tasks": len(task_list.archive),
        "status_counts": status_counts,
        "priority_counts": priority_counts,
    }
