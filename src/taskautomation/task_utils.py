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
    ID_RE,
    METADATA_RE,
    PRIORITY_SECTION_RE,
    ROOT,
    SUBTASK_RE,
    TASK_BLOCK_RE,
    TASKS_FILE,
    TaskInfo,
    find_tasks_by_criteria,
    get_current_datetime,
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
    format_task_block,
    parse_existing_tasks,
)
from .output_formatter import (
    output_result,
)
from .task_types import (
    ExitCode,
    OperationResult,
    ValidationResult,
    create_structured_error,
)
from .validation_utils import (
    validate_prerequisites,
    validate_task_data,
    validate_tasks_file,
    verify_operation_safety,
)

# Re-export all imported functionality for backward compatibility
__all__ = [
    # Constants
    "ROOT",
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
    "ExitCode",
    "ValidationResult",
    "OperationResult",
    # Core functions
    "get_current_datetime",
    "find_tasks_by_criteria",
    # Validation functions
    "validate_task_data",
    "validate_tasks_file",
    "verify_operation_safety",
    "validate_prerequisites",
    # Parsing functions
    "parse_existing_tasks",
    "format_task_block",
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
