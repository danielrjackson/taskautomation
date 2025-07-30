#!/usr/bin/env python3
"""
Markdown parsing utilities for task automation system.

This module provides functions for parsing and formatting task data in the
legacy TASKS.md markdown format used by the task automation system.
"""

from __future__ import annotations

from typing import Any

from .core_utils import (
    METADATA_RE,
    SUBTASK_RE,
    TASK_BLOCK_RE,
    TaskInfo,
)

# =============================================================================
# Task Parsing Functions (Enhanced from run_tests.py)
# =============================================================================


def parse_existing_tasks(task_text: str) -> dict[str, TaskInfo]:
    """
    Parse tasks from TASKS.md content with enhanced validation.

    Args:
        task_text: Content of TASKS.md file

    Returns:
        Dict mapping task title -> TaskInfo
    """
    tasks = {}
    lines = task_text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]
        task_match = TASK_BLOCK_RE.match(line)

        if task_match:
            checked = task_match.group(1) == "x"
            title = task_match.group(2)

            # Initialize task data with defaults
            task_data: dict[str, Any] = {
                "title": title,
                "checked": checked,
                "task_id": -1,
                "priority": "Critical",
                "assignee": None,
                "create_date": None,
                "start_date": None,
                "finish_date": None,
                "estimated_time": None,
                "description": None,
                "prerequisites": [],
                "subtasks": {},
                "raw_block": "",
            }

            # Capture the start of the raw block
            block_start = i

            # Parse task metadata and subtasks
            i += 1
            while i < len(lines):
                line = lines[i]

                # Check for next task or end of current task
                if line.strip() == "" and i + 1 < len(lines) and lines[i + 1].startswith("- ["):
                    break
                if TASK_BLOCK_RE.match(line):
                    i -= 1  # Back up to reprocess this line
                    break

                # Parse metadata
                metadata_match = METADATA_RE.match(line.strip())
                if metadata_match:
                    key = metadata_match.group(1).lower().replace(" ", "_")
                    value = metadata_match.group(2).strip()

                    if key == "id":
                        try:
                            task_data["task_id"] = int(value)
                        except ValueError:
                            task_data["task_id"] = -1
                    elif key in task_data:
                        if value.lower() in ("none", ""):
                            task_data[key] = None
                        else:
                            task_data[key] = value

                # Parse prerequisites
                if line.strip().startswith("- **Pre-requisites**:") or line.strip().startswith(
                    "- **Prerequisites**:"
                ):
                    i += 1
                    while i < len(lines) and lines[i].startswith("    - "):
                        prereq = lines[i].strip()[2:]  # Remove "- "
                        if prereq.lower() != "none":
                            task_data["prerequisites"].append(prereq)
                        i += 1
                    i -= 1  # Back up one line

                # Parse subtasks
                elif line.strip().startswith("- **Subtasks**:"):
                    i += 1
                    while i < len(lines) and lines[i].startswith("    - ["):
                        subtask_match = SUBTASK_RE.match(lines[i])
                        if subtask_match:
                            sub_checked = subtask_match.group(1) == "x"
                            sub_name = subtask_match.group(2)
                            task_data["subtasks"][sub_name] = sub_checked
                        i += 1
                    i -= 1  # Back up one line

                i += 1

            # Capture the raw block
            task_data["raw_block"] = "\n".join(lines[block_start : i + 1])

            # Create TaskInfo object
            task_info = TaskInfo(**task_data)
            tasks[title] = task_info

        i += 1

    return tasks


# =============================================================================
# Task Formatting Functions
# =============================================================================


def format_task_block(task: TaskInfo, updated_subtasks: dict[str, bool] | None = None) -> str:
    """
    Format a TaskInfo object back into markdown task block format.

    Args:
        task: TaskInfo object to format
        updated_subtasks: Optional updated subtask status

    Returns:
        Formatted task block string
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
