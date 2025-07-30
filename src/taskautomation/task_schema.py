#!/usr/bin/env python3
"""
YAML schema definition for task storage system.

This module defines the data structures and validation for task data stored
in YAML format, replacing the regex-based markdown parsing approach.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any


class Priority(enum.StrEnum):

    """Task priority levels."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskStatus(enum.StrEnum):

    """Task completion status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ValidationError(Exception):

    """Custom validation error for task data."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        """Initialize validation error."""
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


def validate_string(
    value: Any,
    field_name: str,
    required: bool = True,
    min_length: int = 0,
    max_length: int | None = None,
) -> str | None:
    """Validate string field."""
    if value is None:
        if required:
            raise ValidationError(f"Field '{field_name}' is required", field_name, value)
        return None

    if not isinstance(value, str):
        raise ValidationError(f"Field '{field_name}' must be a string", field_name, value)

    if len(value) < min_length:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_length} characters", field_name, value
        )

    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"Field '{field_name}' must be at most {max_length} characters", field_name, value
        )

    return value


def validate_integer(
    value: Any, field_name: str, required: bool = True, min_value: int | None = None
) -> int | None:
    """Validate integer field."""
    if value is None:
        if required:
            raise ValidationError(f"Field '{field_name}' is required", field_name, value)
        return None

    if not isinstance(value, int):
        raise ValidationError(f"Field '{field_name}' must be an integer", field_name, value)

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_value}", field_name, value
        )

    return value


def validate_datetime(value: Any, field_name: str, required: bool = True) -> datetime | None:
    """Validate datetime field (accepts ISO format strings)."""
    if value is None:
        if required:
            raise ValidationError(f"Field '{field_name}' is required", field_name, value)
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            # Handle ISO 8601 format with optional Z suffix
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError as e:
            raise ValidationError(
                f"Field '{field_name}' must be a valid ISO 8601 datetime string", field_name, value
            ) from e
    raise ValidationError(
        f"Field '{field_name}' must be a datetime or ISO string", field_name, value
    )


def validate_list(value: Any, field_name: str, required: bool = True) -> list[Any]:
    """Validate list field."""
    if value is None:
        if required:
            raise ValidationError(f"Field '{field_name}' is required", field_name, value)
        return []

    if not isinstance(value, list):
        raise ValidationError(f"Field '{field_name}' must be a list", field_name, value)

    return value


class Subtask:

    """Individual subtask within a main task."""

    def __init__(self, data: dict[str, Any]):
        """Initialize subtask from dictionary."""
        self.name = validate_string(data.get("name"), "name", required=True, min_length=1)
        self.completed = bool(data.get("completed", False))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "completed": self.completed,
        }


class Task:

    """Main task object with full metadata."""

    def __init__(self, data: dict[str, Any]):
        """Initialize task from dictionary."""
        self.id = validate_integer(data.get("id"), "id", required=True, min_value=1)
        self.title = validate_string(
            data.get("title"), "title", required=True, min_length=1, max_length=200
        )
        self.description = validate_string(data.get("description"), "description", required=False)

        # Priority validation
        priority_str = data.get("priority", Priority.MEDIUM.value)
        try:
            self.priority = Priority(priority_str)
        except ValueError as e:
            raise ValidationError(
                f"Invalid priority: {priority_str}", "priority", priority_str
            ) from e

        # Status validation
        status_str = data.get("status", TaskStatus.PENDING.value)
        try:
            self.status = TaskStatus(status_str)
        except ValueError as e:
            raise ValidationError(f"Invalid status: {status_str}", "status", status_str) from e

        self.assignee = validate_string(data.get("assignee"), "assignee", required=False)
        self.estimated_time = validate_string(
            data.get("estimated_time"), "estimated_time", required=False
        )

        # Date handling
        self.created_date = validate_datetime(
            data.get("created_date", datetime.utcnow().isoformat() + "Z"),
            "created_date",
            required=True,
        )
        self.start_date = validate_datetime(data.get("start_date"), "start_date", required=False)
        self.finish_date = validate_datetime(data.get("finish_date"), "finish_date", required=False)

        # Lists
        prerequisites_data = validate_list(
            data.get("prerequisites", []), "prerequisites", required=False
        )
        self.prerequisites = [p.strip() for p in prerequisites_data if p and str(p).strip()]

        tags_data = validate_list(data.get("tags", []), "tags", required=False)
        self.tags = [t.strip().lower() for t in tags_data if t and str(t).strip()]

        # Subtasks
        subtasks_data = validate_list(data.get("subtasks", []), "subtasks", required=False)
        self.subtasks = [Subtask(st) for st in subtasks_data]

        self.notes = validate_string(data.get("notes"), "notes", required=False)

    @property
    def completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    @property
    def subtasks_completed(self) -> int:
        """Count of completed subtasks."""
        return sum(1 for subtask in self.subtasks if subtask.completed)

    @property
    def subtasks_total(self) -> int:
        """Total number of subtasks."""
        return len(self.subtasks)

    @property
    def subtasks_progress(self) -> float:
        """Percentage of subtasks completed (0.0 to 1.0)."""
        if not self.subtasks:
            return 1.0 if self.completed else 0.0
        return self.subtasks_completed / self.subtasks_total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assignee": self.assignee,
            "estimated_time": self.estimated_time,
            "created_date": self.created_date.isoformat() + "Z" if self.created_date else None,
            "start_date": self.start_date.isoformat() + "Z" if self.start_date else None,
            "finish_date": self.finish_date.isoformat() + "Z" if self.finish_date else None,
            "prerequisites": self.prerequisites,
            "tags": self.tags,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "notes": self.notes,
        }


class TaskList:

    """Container for organized task lists by priority."""

    def __init__(self, data: dict[str, Any] | None = None):
        """Initialize task list from dictionary."""
        if data is None:
            data = {}

        self.metadata = data.get("metadata", {})

        # Initialize priority lists
        self.critical = [Task(t) for t in data.get("critical", [])]
        self.high = [Task(t) for t in data.get("high", [])]
        self.medium = [Task(t) for t in data.get("medium", [])]
        self.low = [Task(t) for t in data.get("low", [])]
        self.archive = [Task(t) for t in data.get("archive", [])]

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks across all priority levels."""
        return self.critical + self.high + self.medium + self.low + self.archive

    def get_active_tasks(self) -> list[Task]:
        """Get all non-archived tasks."""
        return self.critical + self.high + self.medium + self.low

    def get_tasks_by_priority(self, priority: Priority) -> list[Task]:
        """Get tasks filtered by priority level."""
        priority_map = {
            Priority.CRITICAL: self.critical,
            Priority.HIGH: self.high,
            Priority.MEDIUM: self.medium,
            Priority.LOW: self.low,
        }
        return priority_map.get(priority, [])

    def get_task_by_id(self, task_id: int) -> Task | None:
        """Find task by ID across all priority levels."""
        for task in self.get_all_tasks():
            if task.id == task_id:
                return task
        return None

    def get_next_task_id(self) -> int:
        """Get the next available task ID."""
        all_tasks = self.get_all_tasks()
        if not all_tasks:
            return 1
        # Filter out None IDs (shouldn't happen with validation, but for type safety)
        task_ids = [task.id for task in all_tasks if task.id is not None]
        return max(task_ids) + 1 if task_ids else 1

    def add_task(self, task: Task) -> None:
        """Add task to appropriate priority list."""
        priority_map = {
            Priority.CRITICAL: self.critical,
            Priority.HIGH: self.high,
            Priority.MEDIUM: self.medium,
            Priority.LOW: self.low,
        }
        target_list = priority_map.get(task.priority)
        if target_list is not None:
            target_list.append(task)

    def archive_task(self, task_id: int) -> bool:
        """Move task to archive by ID."""
        task = self.get_task_by_id(task_id)
        if not task:
            return False

        # Remove from current list
        for priority_list in [self.critical, self.high, self.medium, self.low]:
            if task in priority_list:
                priority_list.remove(task)
                break

        # Add to archive
        task.status = TaskStatus.COMPLETED
        task.finish_date = datetime.utcnow()
        self.archive.append(task)
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata,
            "critical": [t.to_dict() for t in self.critical],
            "high": [t.to_dict() for t in self.high],
            "medium": [t.to_dict() for t in self.medium],
            "low": [t.to_dict() for t in self.low],
            "archive": [t.to_dict() for t in self.archive],
        }


def validate_task_data(data: dict[str, Any]) -> TaskList:
    """
    Validate and parse task data from dictionary.

    Parameters
    ----------
    data : Dict[str, Any]
        Task data dictionary

    Returns
    -------
    TaskList
        Validated TaskList object

    Raises
    ------
    ValidationError
        If data doesn't match schema
    """
    try:
        return TaskList(data)
    except (KeyError, TypeError, ValueError) as e:
        raise ValidationError(f"Invalid task data structure: {e}") from e


def get_schema_example() -> dict[str, Any]:
    """
    Get an example of the expected YAML schema structure.

    Returns
    -------
    Dict[str, Any]
        Example task data structure
    """
    return {
        "metadata": {
            "project_name": "Example Project",
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
        },
        "critical": [
            {
                "id": 1,
                "title": "Fix critical bug",
                "description": "Fix the critical bug in the main module",
                "priority": "Critical",
                "status": "pending",
                "assignee": "Alice",
                "estimated_time": "2 hours",
                "created_date": datetime.utcnow().isoformat() + "Z",
                "prerequisites": ["Setup development environment"],
                "tags": ["bug", "urgent"],
                "subtasks": [
                    {"name": "Identify root cause", "completed": False},
                    {"name": "Write test case", "completed": False},
                    {"name": "Implement fix", "completed": False},
                ],
            }
        ],
        "high": [],
        "medium": [],
        "low": [],
        "archive": [],
    }
