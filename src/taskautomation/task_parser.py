#!/usr/bin/env python3
"""
YAML task parsing functionality for task automation system.

This module handles parsing and manipulating YAML task files using the schema validation system.
Replaces the previous regex-based markdown parsing with robust YAML handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .task_schema import Priority, Task, TaskList, TaskStatus, ValidationError
from .task_types import (
    ExitCode,
    OperationResult,
    TaskOperationResult,
    create_structured_error,
    create_task_operation_error,
)


def parse_yaml_file(file_path: str | Path) -> TaskList:
    """
    Parse a YAML task file and return a validated TaskList.

    Parameters
    ----------
    file_path : str | Path
        Path to the YAML task file

    Returns
    -------
    TaskList
        Validated TaskList object

    Raises
    ------
    ValidationError
        If YAML structure is invalid or fails schema validation
    FileNotFoundError
        If the specified file doesn't exist
    yaml.YAMLError
        If YAML parsing fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Task file not found: {file_path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            # Empty file, return empty TaskList
            return TaskList()

        return TaskList(data)

    except yaml.YAMLError as e:
        raise ValidationError(f"YAML parsing failed: {e}") from e
    except OSError as e:
        raise ValidationError(f"File I/O error: {e}") from e


def parse_yaml_content(content: str) -> TaskList:
    """
    Parse YAML content string and return a validated TaskList.

    Parameters
    ----------
    content : str
        YAML content as string

    Returns
    -------
    TaskList
        Validated TaskList object

    Raises
    ------
    ValidationError
        If YAML structure is invalid or fails schema validation
    yaml.YAMLError
        If YAML parsing fails
    """
    try:
        data = yaml.safe_load(content)

        if data is None:
            # Empty content, return empty TaskList
            return TaskList()

        return TaskList(data)

    except yaml.YAMLError as e:
        raise ValidationError(f"YAML parsing failed: {e}") from e


def save_yaml_file(
    task_list: TaskList, file_path: str | Path, backup: bool = True
) -> OperationResult:
    """
    Save a TaskList to a YAML file with optional backup.

    Parameters
    ----------
    task_list : TaskList
        TaskList object to save
    file_path : str | Path
        Path to save the YAML file
    backup : bool, optional
        Whether to create a backup if file exists, by default True

    Returns
    -------
    OperationResult
        Result of the save operation
    """
    try:
        path = Path(file_path)

        # Create backup if requested and file exists
        if backup and path.exists():
            backup_path = path.with_suffix(f"{path.suffix}.backup")
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save the YAML file
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(
                task_list.to_dict(),
                f,
                default_flow_style=False,
                indent=2,
                sort_keys=False,
                allow_unicode=True,
            )

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message=f"Successfully saved task list to {file_path}",
            data={"file_path": str(file_path), "task_count": len(task_list.get_all_tasks())},
            errors=[],
            warnings=[],
        )

    except OSError as e:
        return create_structured_error(
            f"Failed to save YAML file: {e}", ExitCode.SYSTEM_ERROR, errors=[str(e)]
        )
    except Exception as e:
        return create_structured_error(
            f"Unexpected error saving YAML file: {e}", ExitCode.SYSTEM_ERROR, errors=[str(e)]
        )


def add_task_to_list(
    task_list: TaskList,
    title: str,
    priority: Priority = Priority.MEDIUM,
    description: str | None = None,
    assignee: str | None = None,
    estimated_time: str | None = None,
    prerequisites: list[str] | None = None,
    subtasks: list[dict[str, Any]] | None = None,
) -> TaskOperationResult:
    """
    Add a new task to the TaskList.

    Parameters
    ----------
    task_list : TaskList
        TaskList to add the task to
    title : str
        Task title
    priority : Priority, optional
        Task priority level, by default Priority.MEDIUM
    description : str | None, optional
        Task description, by default None
    assignee : str | None, optional
        Task assignee, by default None
    estimated_time : str | None, optional
        Estimated completion time, by default None
    prerequisites : list[str] | None, optional
        List of prerequisites, by default None
    subtasks : list[dict[str, Any]] | None, optional
        List of subtask data, by default None

    Returns
    -------
    TaskOperationResult
        Result of the add operation
    """
    try:
        # Get next available ID
        next_id = task_list.get_next_task_id()

        # Build task data
        task_data = {
            "id": next_id,
            "title": title,
            "priority": priority.value,
            "status": TaskStatus.PENDING.value,
            "description": description,
            "assignee": assignee,
            "estimated_time": estimated_time,
            "prerequisites": prerequisites or [],
            "subtasks": subtasks or [],
        }

        # Create and validate task
        new_task = Task(task_data)

        # Add to appropriate priority list
        priority_list = getattr(task_list, priority.value.lower())
        priority_list.append(new_task)

        return TaskOperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message=f"Successfully added task: {title}",
            task_list=task_list,
            modified_tasks=[new_task],
            errors=[],
            warnings=[],
        )

    except ValidationError as e:
        return create_task_operation_error(
            f"Failed to add task due to validation error: {e}",
            ExitCode.VALIDATION_ERROR,
            errors=[str(e)],
            task_list=task_list,
        )
    except Exception as e:
        return create_task_operation_error(
            f"Unexpected error adding task: {e}",
            ExitCode.SYSTEM_ERROR,
            errors=[str(e)],
            task_list=task_list,
        )


def update_task_status(
    task_list: TaskList, task_id: int, new_status: TaskStatus
) -> TaskOperationResult:
    """
    Update the status of a task by ID.

    Parameters
    ----------
    task_list : TaskList
        TaskList containing the task
    task_id : int
        ID of the task to update
    new_status : TaskStatus
        New status for the task

    Returns
    -------
    TaskOperationResult
        Result of the update operation
    """
    try:
        task = task_list.get_task_by_id(task_id)
        if task is None:
            return create_task_operation_error(
                f"Task with ID {task_id} not found",
                ExitCode.VALIDATION_ERROR,
                errors=[f"No task found with ID: {task_id}"],
                task_list=task_list,
            )

        # Update status
        old_status = task.status
        task.status = new_status

        return TaskOperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message=f"Updated task {task_id} status from {old_status.value} to {new_status.value}",
            task_list=task_list,
            modified_tasks=[task],
            errors=[],
            warnings=[],
        )

    except Exception as e:
        return create_task_operation_error(
            f"Unexpected error updating task status: {e}",
            ExitCode.SYSTEM_ERROR,
            errors=[str(e)],
            task_list=task_list,
        )


def archive_task(task_list: TaskList, task_id: int) -> TaskOperationResult:
    """
    Archive a task by moving it to the archive section.

    Parameters
    ----------
    task_list : TaskList
        TaskList containing the task
    task_id : int
        ID of the task to archive

    Returns
    -------
    TaskOperationResult
        Result of the archive operation
    """
    try:
        # Get the task before archiving to use in response
        task_to_archive = task_list.get_task_by_id(task_id)
        if task_to_archive is None:
            return create_task_operation_error(
                f"Task with ID {task_id} not found",
                ExitCode.VALIDATION_ERROR,
                errors=[f"No task found with ID: {task_id}"],
                task_list=task_list,
            )

        # Archive the task
        success = task_list.archive_task(task_id)
        if not success:
            return create_task_operation_error(
                f"Failed to archive task with ID {task_id}",
                ExitCode.VALIDATION_ERROR,
                errors=[f"Cannot archive task with ID: {task_id}"],
                task_list=task_list,
            )

        return TaskOperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message=f"Successfully archived task: {task_to_archive.title}",
            task_list=task_list,
            modified_tasks=[task_to_archive],
            errors=[],
            warnings=[],
        )

    except Exception as e:
        return create_task_operation_error(
            f"Unexpected error archiving task: {e}",
            ExitCode.SYSTEM_ERROR,
            errors=[str(e)],
            task_list=task_list,
        )


def find_tasks_by_criteria(
    task_list: TaskList,
    priority: Priority | None = None,
    status: TaskStatus | None = None,
    assignee: str | None = None,
    has_subtasks: bool | None = None,
    include_archived: bool = False,
) -> list[Task]:
    """
    Find tasks matching specified criteria.

    Parameters
    ----------
    task_list : TaskList
        TaskList to search
    priority : Priority | None, optional
        Filter by priority level, by default None
    status : TaskStatus | None, optional
        Filter by task status, by default None
    assignee : str | None, optional
        Filter by assignee, by default None
    has_subtasks : bool | None, optional
        Filter by presence of subtasks, by default None
    include_archived : bool, optional
        Whether to include archived tasks, by default False

    Returns
    -------
    list[Task]
        List of tasks matching the criteria
    """
    # Get tasks to search
    if include_archived:
        tasks = task_list.get_all_tasks() + task_list.archive
    else:
        tasks = task_list.get_all_tasks()

    filtered_tasks = []

    for task in tasks:
        # Apply filters
        if priority is not None and task.priority != priority:
            continue
        if status is not None and task.status != status:
            continue
        if assignee is not None and task.assignee != assignee:
            continue
        if has_subtasks is not None and bool(task.subtasks) != has_subtasks:
            continue

        filtered_tasks.append(task)

    return filtered_tasks


def get_task_summary(task_list: TaskList) -> dict[str, Any]:
    """
    Get comprehensive summary statistics for a TaskList.

    Parameters
    ----------
    task_list : TaskList
        TaskList to summarize

    Returns
    -------
    dict[str, Any]
        Summary statistics including counts by priority, status, and completion rates
    """
    all_tasks = task_list.get_all_tasks()
    archived_tasks = task_list.archive

    # Count by priority
    priority_counts = {}
    for priority in Priority:
        priority_counts[priority.value] = sum(1 for task in all_tasks if task.priority == priority)

    # Count by status
    status_counts = {}
    for status in TaskStatus:
        status_counts[status.value] = sum(1 for task in all_tasks if task.status == status)

    # Calculate completion rate
    total_active = len(all_tasks)
    completed = status_counts.get(TaskStatus.COMPLETED.value, 0)
    completion_rate = (completed / total_active * 100) if total_active > 0 else 0

    return {
        "total_tasks": total_active,
        "archived_tasks": len(archived_tasks),
        "completion_rate": round(completion_rate, 2),
        "priority_breakdown": priority_counts,
        "status_breakdown": status_counts,
        "pending_tasks": status_counts.get(TaskStatus.PENDING.value, 0),
        "in_progress_tasks": status_counts.get(TaskStatus.IN_PROGRESS.value, 0),
        "blocked_tasks": status_counts.get(TaskStatus.BLOCKED.value, 0),
    }


def validate_yaml_structure(content: str) -> OperationResult:
    """
    Validate YAML content structure without creating objects.

    Parameters
    ----------
    content : str
        YAML content to validate

    Returns
    -------
    OperationResult
        Validation result with detailed error information
    """
    try:
        # First, try to parse YAML
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

        # Try to create TaskList for validation
        task_list = TaskList(data)

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="YAML structure is valid",
            data={
                "structure": "valid",
                "task_count": len(task_list.get_all_tasks()),
                "archive_count": len(task_list.archive),
            },
            errors=[],
            warnings=[],
        )

    except yaml.YAMLError as e:
        return create_structured_error(
            "YAML syntax error", ExitCode.VALIDATION_ERROR, errors=[f"YAML parsing failed: {e}"]
        )
    except ValidationError as e:
        return create_structured_error(
            "YAML structure validation failed", ExitCode.VALIDATION_ERROR, errors=[str(e)]
        )
    except Exception as e:
        return create_structured_error(
            "Unexpected validation error", ExitCode.SYSTEM_ERROR, errors=[str(e)]
        )
