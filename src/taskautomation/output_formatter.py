#!/usr/bin/env python3
"""
Output formatting utilities for task automation system.

This module provides output formatting and JSON support functionality extracted
from the original monolithic task_utils.py, including YAML task formatting,
result output, and structured error creation.

Key Features:
- YAML task and task list formatting
- Human and JSON output formats
- Structured error result creation
- ISO8601 datetime formatting
- Comprehensive result display with colors/symbols
- YAML serialization with proper formatting
"""

from __future__ import annotations

import datetime
import json
from typing import Any

import yaml

# Import task types and schema with relative imports for circular import avoidance
from .task_schema import Task, TaskList
from .task_types import ExitCode, OperationResult


def get_current_datetime() -> str:
    """
    Get current datetime in ISO8601 format with Z suffix.

    Returns the current UTC datetime in ISO8601 format, which is compatible
    with various systems and provides timezone-aware timestamps.

    Returns
    -------
    str
        Current datetime string in ISO8601 format with 'Z' suffix
        (e.g., "2024-01-15T10:30:45.123Z")

    Examples
    --------
    >>> timestamp = get_current_datetime()
    >>> print(f"Current time: {timestamp}")
    Current time: 2024-01-15T10:30:45.123Z
    """
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")


def format_task_yaml(task: Task) -> str:
    """
    Format a Task object into YAML string representation.

    Converts a Task schema object into properly formatted YAML string
    for display or file output purposes.

    Parameters
    ----------
    task : Task
        Task schema object to format into YAML

    Returns
    -------
    str
        Formatted YAML string representation of the task

    Examples
    --------
    Format a basic task:
    >>> task = Task(
    ...     id="task-001",
    ...     title="Example Task",
    ...     status="pending",
    ...     priority="high",
    ...     # ... other fields
    ... )
    >>> yaml_str = format_task_yaml(task)
    >>> print(yaml_str)
    id: task-001
    title: Example Task
    status: pending
    priority: high
    ...
    """
    task_dict = task.to_dict()
    return yaml.dump(task_dict, default_flow_style=False, sort_keys=False, indent=2)


def format_task_list_yaml(task_list: TaskList) -> str:
    """
    Format a TaskList object into YAML string representation.

    Converts a TaskList schema object into properly formatted YAML string
    for display or file output purposes.

    Parameters
    ----------
    task_list : TaskList
        TaskList schema object to format into YAML

    Returns
    -------
    str
        Formatted YAML string representation of the task list

    Examples
    --------
    Format a task list:
    >>> task_list = TaskList(
    ...     metadata={"version": "1.0"},
    ...     tasks={"critical": [task1], "high": [task2]}
    ... )
    >>> yaml_str = format_task_list_yaml(task_list)
    >>> print(yaml_str)
    metadata:
      version: "1.0"
    tasks:
      critical:
        - id: task-001
          title: Task 1
          ...
    """
    task_list_dict = task_list.to_dict()
    return yaml.dump(task_list_dict, default_flow_style=False, sort_keys=False, indent=2)


def format_task_block(task: Any, updated_subtasks: dict[str, bool] | None = None) -> str:
    """
    Format a TaskInfo object back into markdown task block format.

    DEPRECATED: This function is maintained for backward compatibility.
    For new YAML-based functionality, use format_task_yaml() instead.

    Converts a legacy TaskInfo object into the standardized markdown format used
    in legacy TASKS.md files, with proper checkbox formatting and metadata structure.

    Parameters
    ----------
    task : Any
        Legacy TaskInfo object to format into markdown (typed as Any for compatibility)
    updated_subtasks : dict[str, bool] | None, optional
        Optional updated subtask status to override task.subtasks.
        If provided, will use this instead of task.subtasks.

    Returns
    -------
    str
        Formatted task block string in markdown format with trailing newline

    Examples
    --------
    Format a basic task:
    >>> task = TaskInfo(
    ...     title="Example Task",
    ...     checked=False,
    ...     task_id=1,
    ...     priority="High",
    ...     # ... other fields
    ... )
    >>> formatted = format_task_block(task)
    >>> print(formatted)
    - [ ] **Example Task**:
      - **ID**: 1
      - **Description**: No description
      ...
    """
    subtasks = updated_subtasks if updated_subtasks is not None else task.subtasks

    # Determine main task checkbox
    main_checked = "[x]" if task.checked else "[ ]"

    lines = [
        f"- {main_checked} **{task.title}**:",
        f"  - **ID**: {task.task_id}",
        f"  - **Description**: {task.description or 'No description'}",
        "  - **Pre-requisites**:",
    ]

    # Add prerequisites
    if task.prerequisites:
        for prereq in task.prerequisites:
            lines.append(f"    - {prereq}")
    else:
        lines.append("    - None")

    lines.extend(
        [
            f"  - **Priority**: {task.priority}",
            f"  - **Estimated Time**: {task.estimated_time or '30 minutes'}",
            f"  - **Assignee**: {task.assignee or 'None'}",
            f"  - **Create Date**: {task.create_date or 'None'}",
            f"  - **Start Date**: {task.start_date or 'None'}",
            f"  - **Finish Date**: {task.finish_date or 'None'}",
            "  - **Subtasks**:",
        ]
    )

    # Add subtasks
    if subtasks:
        for subtask_name, is_checked in subtasks.items():
            checkbox = "[x]" if is_checked else "[ ]"
            lines.append(f"    - {checkbox} {subtask_name}")
    else:
        lines.append("    - None")

    return "\n".join(lines) + "\n"


def format_task_summary(task: Task, include_subtasks: bool = True) -> str:
    """
    Format a Task object into a human-readable summary.

    Creates a concise, human-friendly representation of a task with key details
    and optional subtask information.

    Parameters
    ----------
    task : Task
        Task schema object to summarize
    include_subtasks : bool, optional
        Whether to include subtask details in the summary, by default True

    Returns
    -------
    str
        Formatted task summary string

    Examples
    --------
    Format a task summary:
    >>> task = Task(
    ...     id="task-001",
    ...     title="Example Task",
    ...     status="in_progress",
    ...     priority="high"
    ... )
    >>> summary = format_task_summary(task)
    >>> print(summary)
    [task-001] Example Task (HIGH PRIORITY, IN PROGRESS)
    Description: No description provided
    ...
    """
    lines = []

    # Header line with ID, title, priority, and status
    priority_text = task.priority.upper() if task.priority else "UNKNOWN"
    status_text = task.status.upper().replace("_", " ") if task.status else "UNKNOWN"

    header = f"[{task.id}] {task.title or 'Untitled Task'}"
    if task.priority or task.status:
        header += f" ({priority_text} PRIORITY, {status_text})"
    lines.append(header)

    # Description
    description = task.description or "No description provided"
    lines.append(f"Description: {description}")

    # Dates if available
    if task.created_date:
        lines.append(f"Created: {task.created_date}")
    if task.start_date:
        lines.append(f"Start: {task.start_date}")
    if task.finish_date:
        lines.append(f"Finish: {task.finish_date}")

    # Prerequisites
    if task.prerequisites:
        lines.append(f"Prerequisites: {', '.join(task.prerequisites)}")

    # Subtasks
    if include_subtasks and task.subtasks:
        lines.append("Subtasks:")
        for subtask in task.subtasks:
            status_symbol = "✓" if subtask.completed else "○"
            lines.append(f"  {status_symbol} {subtask.name}")

    return "\n".join(lines)


def format_task_list_summary(task_list: TaskList, group_by_priority: bool = True) -> str:
    """
    Format a TaskList object into a human-readable summary.

    Creates a comprehensive overview of all tasks in the task list, optionally
    grouped by priority level for better organization.

    Parameters
    ----------
    task_list : TaskList
        TaskList schema object to summarize
    group_by_priority : bool, optional
        Whether to group tasks by priority level, by default True

    Returns
    -------
    str
        Formatted task list summary string

    Examples
    --------
    Format a task list summary:
    >>> task_list = TaskList(
    ...     metadata={"version": "1.0"},
    ...     tasks={"critical": [task1], "high": [task2]}
    ... )
    >>> summary = format_task_list_summary(task_list)
    >>> print(summary)
    Task List Summary
    =================
    Total Tasks: 2

    CRITICAL PRIORITY (1 tasks)
    - [task-001] Critical Task (PENDING)
    ...
    """
    lines = ["Task List Summary", "=" * 17]

    # Get all tasks and count by priority and status
    all_tasks = task_list.get_all_tasks()
    total_tasks = len(all_tasks)

    # Count by priority and status
    priority_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for task in all_tasks:
        # Count by priority
        priority = task.priority.value if task.priority else "unknown"
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Count by status
        status = task.status.value if task.status else "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    lines.append(f"Total Tasks: {total_tasks}")

    # Status breakdown
    if status_counts:
        status_parts = []
        for status, count in sorted(status_counts.items()):
            status_parts.append(f"{count} {status.replace('_', ' ').title()}")
        lines.append(f"Status: {', '.join(status_parts)}")

    lines.append("")  # Empty line

    # Group by priority if requested
    if group_by_priority:
        priority_lists = [
            ("Critical", task_list.critical),
            ("High", task_list.high),
            ("Medium", task_list.medium),
            ("Low", task_list.low),
        ]

        for priority_name, tasks in priority_lists:
            if tasks:
                lines.append(f"{priority_name.upper()} PRIORITY ({len(tasks)} tasks)")

                for task in tasks:
                    status_text = (
                        task.status.value.upper().replace("_", " ") if task.status else "UNKNOWN"
                    )
                    lines.append(f"- [{task.id}] {task.title or 'Untitled'} ({status_text})")

                lines.append("")  # Empty line between priority groups

        # Show archive summary if it exists
        if task_list.archive:
            lines.append(f"ARCHIVED ({len(task_list.archive)} tasks)")
            lines.append("")
    else:
        # Flat list of all active tasks
        for task in task_list.get_active_tasks():
            priority_text = task.priority.value.upper() if task.priority else "UNKNOWN"
            status_text = task.status.value.upper().replace("_", " ") if task.status else "UNKNOWN"
            lines.append(
                f"- [{task.id}] {task.title or 'Untitled'} ({priority_text}, {status_text})"
            )

    return "\n".join(lines)


def output_result(result: OperationResult, format_type: str = "human", quiet: bool = False) -> None:
    """
    Output operation result in specified format.

    Displays operation results in either human-readable format with colors
    and symbols, or machine-readable JSON format for programmatic consumption.

    Parameters
    ----------
    result : OperationResult
        OperationResult object containing operation outcome and details
    format_type : str, optional
        Output format type, either "human" or "json", by default "human"
    quiet : bool, optional
        If True, suppress non-essential output in human format, by default False

    Examples
    --------
    Output successful result in human format:
    >>> result = OperationResult(
    ...     success=True,
    ...     exit_code=ExitCode.SUCCESS,
    ...     message="Operation completed",
    ...     data={},
    ...     errors=[],
    ...     warnings=[]
    ... )
    >>> output_result(result)
    ✓ Operation completed

    Output result in JSON format:
    >>> output_result(result, format_type="json")
    {
      "success": true,
      "exit_code": 0,
      "message": "Operation completed",
      ...
    }
    """
    if format_type == "json":
        output_data = {
            "success": result.success,
            "exit_code": result.exit_code.value,
            "message": result.message,
            "data": result.data,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        print(json.dumps(output_data, indent=2))
    else:
        # Human format
        if not quiet:
            if result.success:
                print(f"✓ {result.message}")
            else:
                print(f"✗ {result.message}")

            if result.warnings and not quiet:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  ⚠ {warning}")

            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  ✗ {error}")


def create_structured_error(
    message: str,
    exit_code: ExitCode,
    errors: list[str] | None = None,
    context: dict[str, Any] | None = None,
) -> OperationResult:
    """
    Create a structured error result.

    Constructs a standardized OperationResult object for error conditions,
    ensuring consistent error reporting across the automation system.

    Parameters
    ----------
    message : str
        Main error message describing the failure
    exit_code : ExitCode
        Appropriate exit code for the error type
    errors : list[str] | None, optional
        List of detailed error messages, by default None
    context : dict[str, Any] | None, optional
        Additional context data related to the error, by default None

    Returns
    -------
    OperationResult
        OperationResult object configured for error state with:
        - success=False
        - provided exit_code
        - provided message and errors
        - empty warnings list
        - context data (or empty dict if None)

    Examples
    --------
    Create a validation error:
    >>> error_result = create_structured_error(
    ...     message="Validation failed",
    ...     exit_code=ExitCode.VALIDATION_ERROR,
    ...     errors=["Missing required field: title"],
    ...     context={"file": "TASKS.md"}
    ... )
    >>> print(f"Success: {error_result.success}")
    Success: False
    """
    return OperationResult(
        success=False,
        exit_code=exit_code,
        message=message,
        data=context or {},
        errors=errors or [],
        warnings=[],
    )


def format_validation_summary(
    validation_results: list[tuple[str, bool, list[str], list[str]]],
) -> str:
    """
    Format multiple validation results into a human-readable summary.

    Creates a formatted summary of validation results from multiple sources,
    useful for displaying comprehensive validation reports.

    Parameters
    ----------
    validation_results : list[tuple[str, bool, list[str], list[str]]]
        List of validation results, each tuple containing:
        - source_name (str): Name of the validation source
        - is_valid (bool): Whether validation passed
        - errors (list[str]): List of error messages
        - warnings (list[str]): List of warning messages

    Returns
    -------
    str
        Formatted validation summary with symbols and indentation

    Examples
    --------
    >>> results = [
    ...     ("File Structure", True, [], ["Missing optional file"]),
    ...     ("Task Format", False, ["Invalid ID"], []),
    ... ]
    >>> summary = format_validation_summary(results)
    >>> print(summary)
    Validation Summary:
    ✓ File Structure (1 warning)
      ⚠ Missing optional file
    ✗ Task Format (1 error)
      ✗ Invalid ID
    """
    lines = ["Validation Summary:"]

    for source_name, is_valid, errors, warnings in validation_results:
        # Status line
        symbol = "✓" if is_valid else "✗"
        error_count = len(errors)
        warning_count = len(warnings)

        status_parts = []
        if error_count > 0:
            status_parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
        if warning_count > 0:
            status_parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")

        status_text = f" ({', '.join(status_parts)})" if status_parts else ""
        lines.append(f"{symbol} {source_name}{status_text}")

        # Error details
        for error in errors:
            lines.append(f"  ✗ {error}")

        # Warning details
        for warning in warnings:
            lines.append(f"  ⚠ {warning}")

    return "\n".join(lines)


def create_success_result(
    message: str,
    data: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> OperationResult:
    """
    Create a structured success result.

    Constructs a standardized OperationResult object for successful operations,
    ensuring consistent success reporting across the automation system.

    Parameters
    ----------
    message : str
        Success message describing the completed operation
    data : dict[str, Any] | None, optional
        Additional data related to the successful operation, by default None
    warnings : list[str] | None, optional
        List of warning messages (operation succeeded but with caveats), by default None

    Returns
    -------
    OperationResult
        OperationResult object configured for success state with:
        - success=True
        - exit_code=ExitCode.SUCCESS
        - provided message and warnings
        - empty errors list
        - context data (or empty dict if None)

    Examples
    --------
    Create a simple success result:
    >>> success_result = create_success_result(
    ...     message="Task completed successfully",
    ...     data={"task_id": 42},
    ...     warnings=["Some optional steps were skipped"]
    ... )
    >>> print(f"Success: {success_result.success}")
    Success: True
    """
    return OperationResult(
        success=True,
        exit_code=ExitCode.SUCCESS,
        message=message,
        data=data or {},
        errors=[],
        warnings=warnings or [],
    )
