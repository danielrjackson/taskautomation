#!/usr/bin/env python3
"""
Core utilities for task automation with unique data structures and patterns.

This module contains core data structures and utilities that are specific to the
task automation system and not covered by the other specialized modules.
"""

from __future__ import annotations

import datetime
import pathlib
import re
from typing import NamedTuple

# =============================================================================
# Path Constants and Configuration
# =============================================================================

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASKS_FILE = ROOT / "docs" / "TASKS.md"
BACKUP_DIR = ROOT / ".task_backups"


# =============================================================================
# Regex Patterns for Markdown Parsing
# =============================================================================

# Regex patterns for parsing TASKS.md format - enhanced for validation
TASK_BLOCK_RE = re.compile(r"- \[([ x])\] \*\*(.+?)\*\*:", re.M)
SUBTASK_RE = re.compile(r"    - \[([ x])\] (.+?)(?:\n|$)", re.M)
ID_RE = re.compile(r"- \*\*ID\*\*: (\d+)", re.M)
PRIORITY_SECTION_RE = re.compile(r"^## (.+) Priority Tasks?$", re.M)
ARCHIVE_SECTION_RE = re.compile(r"^## Archive$", re.M)

# Enhanced patterns for comprehensive parsing
METADATA_RE = re.compile(r"- \*\*(.+?)\*\*: (.+?)(?:\n|$)", re.M)
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?$")


# =============================================================================
# Task Data Structures
# =============================================================================


class TaskInfo(NamedTuple):
    """Enhanced task information with full metadata and validation."""

    title: str
    checked: bool
    task_id: int
    priority: str
    assignee: str | None
    create_date: str | None
    start_date: str | None
    finish_date: str | None
    estimated_time: str | None
    description: str | None
    prerequisites: list[str]
    subtasks: dict[str, bool]  # subtask_name -> checked
    raw_block: str  # Original text block for preservation


# =============================================================================
# Datetime Utilities
# =============================================================================


def get_current_datetime() -> str:
    """
    Get current datetime in ISO8601 format with Z suffix.

    Returns:
        Current datetime string
    """
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")


# =============================================================================
# Task Filtering Utilities
# =============================================================================


def find_tasks_by_criteria(
    tasks: dict[str, TaskInfo],
    priority: str | None = None,
    checked: bool | None = None,
    assignee: str | None = None,
    has_subtasks: bool | None = None,
) -> dict[str, TaskInfo]:
    """
    Filter tasks by various criteria.

    Args:
        tasks: Dictionary of tasks to filter
        priority: Filter by priority level
        checked: Filter by completion status
        assignee: Filter by assignee
        has_subtasks: Filter by presence of subtasks

    Returns:
        Filtered dictionary of tasks
    """
    filtered = {}

    for title, task in tasks.items():
        # Apply filters
        if priority is not None and task.priority != priority:
            continue
        if checked is not None and task.checked != checked:
            continue
        if assignee is not None and task.assignee != assignee:
            continue
        if has_subtasks is not None and bool(task.subtasks) != has_subtasks:
            continue

        filtered[title] = task

    return filtered
