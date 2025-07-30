#!/usr/bin/env python3
"""
Shared utilities for task automation scripts with validation-first approach.

This module provides common functionality for all task management scripts, with
emphasis on validation, error handling, and "check your work" capabilities.

Key Features:
- Comprehensive task validation with detailed error reporting
- Dry-run mode support for safe operation
- AI-friendly JSON output and structured errors
- Backup and recovery mechanisms
- Git integration helpers
- Standardized exit codes
"""

from __future__ import annotations

import collections
import datetime
import enum
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any, NamedTuple

# =============================================================================
# Constants and Configuration
# =============================================================================

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASKS_FILE = ROOT / "docs" / "TASKS.md"
BACKUP_DIR = ROOT / ".task_backups"
PYPROJECT_FILE = ROOT / "pyproject.toml"

# Regex patterns from run_tests.py - enhanced for validation
TASK_BLOCK_RE = re.compile(r"- \[([ x])\] \*\*(.+?)\*\*:", re.M)
SUBTASK_RE = re.compile(r"    - \[([ x])\] (.+?)(?:\n|$)", re.M)
ID_RE = re.compile(r"- \*\*ID\*\*: (\d+)", re.M)
PRIORITY_SECTION_RE = re.compile(r"^## (.+) Priority Tasks?$", re.M)
ARCHIVE_SECTION_RE = re.compile(r"^## Archive$", re.M)

# Enhanced patterns for comprehensive parsing
METADATA_RE = re.compile(r"- \*\*(.+?)\*\*: (.+?)(?:\n|$)", re.M)
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?$")


# =============================================================================
# Data Structures
# =============================================================================


class ExitCode(enum.IntEnum):
    """Standardized exit codes for all automation scripts."""

    SUCCESS = 0  # Operation completed successfully
    NO_WORK = 1  # No work needed (e.g., all tasks completed)
    VALIDATION_ERROR = 2  # Validation failed (bad data, missing requirements)
    SYSTEM_ERROR = 3  # System error (file I/O, git, etc.)
    USER_ABORT = 4  # User aborted operation


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


# =============================================================================
# Core Validation Functions
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


def validate_tasks_file(file_path: pathlib.Path | None = None) -> ValidationResult:
    """
    Validate the entire tasks file structure and content.

    Args:
        file_path: Path to tasks file (defaults to TASKS_FILE)

    Returns:
        ValidationResult with file-level validation information
    """
    if file_path is None:
        file_path = TASKS_FILE

    errors = []
    warnings = []
    context = {"file_path": str(file_path)}

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
        tasks = parse_existing_tasks(content)
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
# File Operations with Validation
# =============================================================================


def backup_tasks_file(backup_suffix: str | None = None) -> pathlib.Path:
    """
    Create a timestamped backup of the tasks file.

    Args:
        backup_suffix: Optional suffix for backup filename

    Returns:
        Path to the created backup file

    Raises:
        FileNotFoundError: If tasks file doesn't exist
        OSError: If backup creation fails
    """
    if not TASKS_FILE.exists():
        raise FileNotFoundError(f"Tasks file not found: {TASKS_FILE}")

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    suffix = f"_{backup_suffix}" if backup_suffix else ""
    backup_name = f"TASKS_{timestamp}{suffix}.md"
    backup_path = BACKUP_DIR / backup_name

    # Create backup
    shutil.copy2(TASKS_FILE, backup_path)

    return backup_path


def load_tasks_file(
    file_path: pathlib.Path | None = None, validate: bool = True
) -> tuple[str, dict[str, TaskInfo]]:
    """
    Load and parse tasks file with optional validation.

    Args:
        file_path: Path to tasks file (defaults to TASKS_FILE)
        validate: Whether to validate the file content

    Returns:
        Tuple of (file_content, parsed_tasks)

    Raises:
        FileNotFoundError: If tasks file doesn't exist
        ValueError: If validation fails and validate=True
    """
    if file_path is None:
        file_path = TASKS_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    if validate:
        validation = validate_tasks_file(file_path)
        if not validation.is_valid:
            error_msg = "Tasks file validation failed:\n" + "\n".join(validation.errors)
            raise ValueError(error_msg)

    tasks = parse_existing_tasks(content)
    return content, tasks


def save_tasks_file(
    content: str,
    file_path: pathlib.Path | None = None,
    backup: bool = True,
    validate: bool = True,
    dry_run: bool = False,
) -> OperationResult:
    """
    Save tasks file with validation and backup.

    Args:
        content: New file content
        file_path: Path to tasks file (defaults to TASKS_FILE)
        backup: Whether to create backup before saving
        validate: Whether to validate content before saving
        dry_run: If True, don't actually save the file

    Returns:
        OperationResult with operation details
    """
    if file_path is None:
        file_path = TASKS_FILE

    errors = []
    warnings = []
    data = {"file_path": str(file_path), "dry_run": dry_run}

    # Validate content if requested
    if validate:
        # Write to temp file for validation
        temp_file = file_path.with_suffix(".tmp")
        try:
            temp_file.write_text(content, encoding="utf-8")
            validation = validate_tasks_file(temp_file)
            temp_file.unlink()  # Clean up temp file

            if not validation.is_valid:
                errors.extend(validation.errors)
                return OperationResult(
                    success=False,
                    exit_code=ExitCode.VALIDATION_ERROR,
                    message="Content validation failed",
                    data=data,
                    errors=errors,
                    warnings=validation.warnings,
                )
            warnings.extend(validation.warnings)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            errors.append(f"Validation error: {e}")
            return OperationResult(
                success=False,
                exit_code=ExitCode.SYSTEM_ERROR,
                message="Validation system error",
                data=data,
                errors=errors,
                warnings=warnings,
            )

    if dry_run:
        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="Dry run - file would be saved",
            data=data,
            errors=errors,
            warnings=warnings,
        )

    try:
        # Create backup if requested and file exists
        backup_path = None
        if backup and file_path.exists():
            backup_path = backup_tasks_file("pre_save")
            data["backup_path"] = str(backup_path)

        # Save file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="Tasks file saved successfully",
            data=data,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Save error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.SYSTEM_ERROR,
            message="File save failed",
            data=data,
            errors=errors,
            warnings=warnings,
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
            task_data = {
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


# =============================================================================
# Git Integration Helpers
# =============================================================================


def run_git_command(cmd: list[str]) -> tuple[bool, str, str]:
    """
    Run a git command safely and return results.

    Args:
        cmd: Git command as list of strings

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + cmd, capture_output=True, text=True, check=False, cwd=ROOT
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def get_git_info() -> dict[str, str]:
    """
    Get current git repository information.

    Returns:
        Dictionary with git information
    """
    info = {
        "branch": "unknown",
        "commit": "unknown",
        "user_name": "unknown",
        "user_email": "unknown",
        "is_clean": False,
        "has_uncommitted": False,
    }

    # Get branch
    success, branch, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if success:
        info["branch"] = branch

    # Get commit
    success, commit, _ = run_git_command(["rev-parse", "HEAD"])
    if success:
        info["commit"] = commit[:8]  # Short hash

    # Get user info
    success, name, _ = run_git_command(["config", "user.name"])
    if success:
        info["user_name"] = name

    success, email, _ = run_git_command(["config", "user.email"])
    if success:
        info["user_email"] = email

    # Check if working directory is clean
    success, status, _ = run_git_command(["status", "--porcelain"])
    if success:
        info["is_clean"] = len(status) == 0
        info["has_uncommitted"] = len(status) > 0

    return info


def get_current_branch() -> str:
    """
    Get current git branch name with fallback.

    Returns:
        Current branch name or "unknown-branch"
    """
    success, branch, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    return branch if success else "unknown-branch"


# =============================================================================
# Output and Formatting Functions
# =============================================================================


def get_current_datetime() -> str:
    """
    Get current datetime in ISO8601 format with Z suffix.

    Returns:
        Current datetime string
    """
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")


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


def output_result(result: OperationResult, format_type: str = "human", quiet: bool = False) -> None:
    """
    Output operation result in specified format.

    Args:
        result: OperationResult to output
        format_type: Output format ("human" or "json")
        quiet: Suppress non-essential output
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

    Args:
        message: Main error message
        exit_code: Appropriate exit code
        errors: List of detailed errors
        context: Additional context data

    Returns:
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


# =============================================================================
# Check Your Work Functions
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


def validate_prerequisites() -> ValidationResult:
    """
    Validate that all prerequisites for task operations are met.

    Returns:
        ValidationResult with prerequisite check results
    """
    errors = []
    warnings = []
    context = {}

    # Check Python version
    python_version = sys.version_info
    context["python_version"] = (
        f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version < (3, 8):
        errors.append(f"Python 3.8+ required, found {context['python_version']}")

    # Check required directories
    required_dirs = [ROOT / "docs", ROOT / "scripts" / "dev"]
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


# Missing import for os module
import os
