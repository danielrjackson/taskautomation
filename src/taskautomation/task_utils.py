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

# Import core functionality from specialized modules
from .core_utils import (
    ARCHIVE_SECTION_RE,
    BACKUP_DIR,
    DATETIME_RE,
    DOCS_DIR,
    ID_RE,
    METADATA_RE,
    PLANNING_DIR,
    PRIORITY_SECTION_RE,
    ROOT,
    ROOT_DIR,
    SRC_DIR,
    SUBTASK_RE,
    TASK_BLOCK_RE,
    TASKS_FILE,
    TaskInfo,
    find_tasks_by_criteria,
    format_iso8601_datetime,
    get_current_datetime,
    get_git_root,
)
from .file_operations import (
    backup_tasks_file,
    load_tasks_file,
    save_tasks_file,
)
from .git_helpers import (
    get_current_branch,
    get_git_info,
    run_git_command,
)
from .markdown_parser import (
    convert_legacy_to_new_format,
    format_task_block,
    parse_existing_tasks,
    parse_legacy_task_format,
    parse_tasks_from_markdown,
)
from .output_formatter import (
    output_result,
)
from .task_schema import Priority, TaskStatus
from .task_types import (
    ExitCode,
    OperationResult,
    ValidationResult,
    create_structured_error,
)
from .validation_utils import (
    extract_assignee,
    extract_create_date,
    extract_description,
    extract_finished_date,
    extract_priority,
    extract_task_id,
    is_valid_task_line,
    validate_prerequisites,
    validate_task_data,
    validate_task_format,
    validate_task_schema,
    validate_tasks_file,
    verify_operation_safety,
)

# Re-export all imported functionality for backward compatibility
__all__ = [
    # Constants
    "ROOT",
    "ROOT_DIR",
    "DOCS_DIR",
    "SRC_DIR",
    "PLANNING_DIR",
    "TASKS_FILE",
    "BACKUP_DIR",
    # Regex patterns
    "TASK_BLOCK_RE",
    "SUBTASK_RE",
    "ID_RE",
    "PRIORITY_SECTION_RE",
    "ARCHIVE_SECTION_RE",
    "METADATA_RE",
    "DATETIME_RE",
    # Data structures
    "TaskInfo",
    "Priority",
    "TaskStatus",
    "ExitCode",
    "ValidationResult",
    "OperationResult",
    # Core functions
    "format_iso8601_datetime",
    "get_current_datetime",
    "get_git_root",
    "get_default_root",
    "find_tasks_by_criteria",
    # Validation functions
    "is_valid_task_line",
    "validate_task_data",
    "validate_task_format",
    "validate_task_schema",
    "validate_tasks_file",
    "verify_operation_safety",
    "validate_prerequisites",
    "extract_assignee",
    "extract_create_date",
    "extract_description",
    "extract_finished_date",
    "extract_priority",
    "extract_task_id",
    # Parsing functions
    "parse_existing_tasks",
    "parse_legacy_task_format",
    "parse_tasks_from_markdown",
    "format_task_block",
    "convert_legacy_to_new_format",
    # Git functions
    "run_git_command",
    "get_git_info",
    "get_current_branch",
    # Output functions
    "output_result",
    "create_structured_error",
    # File operations
    "backup_tasks_file",
    "load_tasks_file",
    "save_tasks_file",
]


# =============================================================================
# Additional utility functions for backward compatibility
# =============================================================================


def get_default_root() -> str:
    """
    Get the default root directory for the project.

    Returns:
        String path to the project root directory
    """
    return str(ROOT)
