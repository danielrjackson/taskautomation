#!/usr/bin/env python3
"""
File operations module for task automation system.

This module provides safe file I/O operations with backup/recovery mechanisms,
validation, and safety checks for YAML-based task management files.

Key Features:
- Atomic YAML file operations with backup support
- Schema validation-first approach for all file operations
- Safe directory and permission handling
- System prerequisite validation
- Temporary file handling for validation
- YAML serialization/deserialization with proper formatting
"""

from __future__ import annotations

import datetime
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any

import yaml

from .task_schema import TaskList
from .task_types import ExitCode, OperationResult, ValidationResult

# =============================================================================
# Constants
# =============================================================================

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASKS_FILE = ROOT / "docs" / "tasks.yaml"
BACKUP_DIR = ROOT / ".task_backups"


# =============================================================================
# File Backup Operations
# =============================================================================


def backup_tasks_file(backup_suffix: str | None = None) -> pathlib.Path:
    """
    Create a timestamped backup of the YAML tasks file.

    Parameters
    ----------
    backup_suffix : str | None, optional
        Optional suffix for backup filename, by default None

    Returns
    -------
    pathlib.Path
        Path to the created backup file

    Raises
    ------
    FileNotFoundError
        If tasks file doesn't exist
    OSError
        If backup creation fails
    """
    if not TASKS_FILE.exists():
        raise FileNotFoundError(f"Tasks file not found: {TASKS_FILE}")

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    suffix = f"_{backup_suffix}" if backup_suffix else ""
    backup_name = f"tasks_{timestamp}{suffix}.yaml"
    backup_path = BACKUP_DIR / backup_name

    # Create backup
    shutil.copy2(TASKS_FILE, backup_path)

    return backup_path


def restore_tasks_file(backup_path: pathlib.Path) -> OperationResult:
    """
    Restore tasks file from backup.

    Parameters
    ----------
    backup_path : pathlib.Path
        Path to backup file to restore from

    Returns
    -------
    OperationResult
        OperationResult with restoration details
    """
    errors: list[str] = []
    warnings: list[str] = []
    data: dict[str, Any] = {"backup_path": str(backup_path), "target_path": str(TASKS_FILE)}

    try:
        if not backup_path.exists():
            errors.append(f"Backup file not found: {backup_path}")
            return OperationResult(
                success=False,
                exit_code=ExitCode.SYSTEM_ERROR,
                message="Backup file not found",
                data=data,
                errors=errors,
                warnings=warnings,
            )

        # Create backup of current file before restoring
        if TASKS_FILE.exists():
            try:
                current_backup = backup_tasks_file("pre_restore")
                data["current_backup"] = str(current_backup)
                warnings.append(f"Current file backed up to: {current_backup}")
            except Exception as e:
                warnings.append(f"Could not backup current file: {e}")

        # Restore from backup
        shutil.copy2(backup_path, TASKS_FILE)

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="Tasks file restored successfully",
            data=data,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Restore error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.SYSTEM_ERROR,
            message="File restore failed",
            data=data,
            errors=errors,
            warnings=warnings,
        )


# =============================================================================
# File Loading Operations
# =============================================================================


def load_tasks_file(
    file_path: pathlib.Path | None = None, validate: bool = True
) -> tuple[TaskList, dict[str, Any]]:
    """
    Load and parse YAML tasks file with optional schema validation.

    Parameters
    ----------
    file_path : pathlib.Path | None, optional
        Path to tasks YAML file (defaults to TASKS_FILE), by default None
    validate : bool, optional
        Whether to validate the file content against schema, by default True

    Returns
    -------
    tuple[TaskList, dict[str, Any]]
        Tuple of (parsed_task_list, raw_yaml_data)

    Raises
    ------
    FileNotFoundError
        If tasks file doesn't exist
    ValueError
        If validation fails and validate=True
    yaml.YAMLError
        If YAML parsing fails
    """
    if file_path is None:
        file_path = TASKS_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {file_path}")

    # Load YAML content
    try:
        with open(file_path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML file {file_path}: {e}")

    if validate:
        # Import here to avoid circular imports
        from .task_validator import validate_yaml_content

        validation = validate_yaml_content(raw_data)
        if not validation.is_valid:
            error_msg = "Tasks file validation failed:\n" + "\n".join(validation.errors)
            raise ValueError(error_msg)

    # Import here to avoid circular imports
    from .task_parser import parse_yaml_tasks

    task_list = parse_yaml_tasks(raw_data)
    return task_list, raw_data


def read_file_safely(file_path: pathlib.Path, encoding: str = "utf-8") -> OperationResult:
    """
    Safely read a file with error handling.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to file to read
    encoding : str, optional
        File encoding to use, by default "utf-8"

    Returns
    -------
    OperationResult
        OperationResult with file content in data['content']
    """
    errors: list[str] = []
    warnings: list[str] = []
    data: dict[str, Any] = {"file_path": str(file_path), "encoding": encoding}

    try:
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return OperationResult(
                success=False,
                exit_code=ExitCode.SYSTEM_ERROR,
                message="File not found",
                data=data,
                errors=errors,
                warnings=warnings,
            )

        if not file_path.is_file():
            errors.append(f"Path is not a file: {file_path}")
            return OperationResult(
                success=False,
                exit_code=ExitCode.SYSTEM_ERROR,
                message="Path is not a file",
                data=data,
                errors=errors,
                warnings=warnings,
            )

        content = file_path.read_text(encoding=encoding)
        data["content"] = content
        data["size"] = len(content)
        data["lines"] = len(content.split("\n"))

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="File read successfully",
            data=data,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Read error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.SYSTEM_ERROR,
            message="File read failed",
            data=data,
            errors=errors,
            warnings=warnings,
        )


# =============================================================================
# File Saving Operations
# =============================================================================


def save_tasks_file(
    task_list: TaskList,
    file_path: pathlib.Path | None = None,
    backup: bool = True,
    validate: bool = True,
    dry_run: bool = False,
) -> OperationResult:
    """
    Save YAML tasks file with schema validation and backup.

    Parameters
    ----------
    task_list : TaskList
        TaskList object to save as YAML
    file_path : pathlib.Path | None, optional
        Path to tasks file (defaults to TASKS_FILE), by default None
    backup : bool, optional
        Whether to create backup before saving, by default True
    validate : bool, optional
        Whether to validate content before saving, by default True
    dry_run : bool, optional
        If True, don't actually save the file, by default False

    Returns
    -------
    OperationResult
        OperationResult with operation details
    """
    if file_path is None:
        file_path = TASKS_FILE

    errors: list[str] = []
    warnings: list[str] = []
    data: dict[str, Any] = {"file_path": str(file_path), "dry_run": dry_run}

    try:
        # Convert TaskList to dict for YAML serialization
        yaml_data = task_list.to_dict()

        # Validate content if requested
        if validate:
            # Import here to avoid circular imports
            from .task_validator import validate_task_list

            validation = validate_task_list(task_list)
            if not validation.is_valid:
                errors.extend(validation.errors)
                return OperationResult(
                    success=False,
                    exit_code=ExitCode.VALIDATION_ERROR,
                    message="TaskList validation failed",
                    data=data,
                    errors=errors,
                    warnings=validation.warnings,
                )
            warnings.extend(validation.warnings)

        if dry_run:
            # Show what would be saved in dry run
            yaml_content = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False, indent=2)
            data["yaml_preview"] = (
                yaml_content[:500] + "..." if len(yaml_content) > 500 else yaml_content
            )
            return OperationResult(
                success=True,
                exit_code=ExitCode.SUCCESS,
                message="Dry run - file would be saved",
                data=data,
                errors=errors,
                warnings=warnings,
            )

        # Create backup if requested and file exists
        backup_path = None
        if backup and file_path.exists():
            backup_path = backup_tasks_file("pre_save")
            data["backup_path"] = str(backup_path)

        # Save YAML file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, indent=2)

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="YAML tasks file saved successfully",
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


def write_file_safely(
    file_path: pathlib.Path,
    content: str,
    encoding: str = "utf-8",
    backup: bool = False,
    create_dirs: bool = True,
) -> OperationResult:
    """
    Safely write content to a file with error handling.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to file to write
    content : str
        Content to write
    encoding : str, optional
        File encoding to use, by default "utf-8"
    backup : bool, optional
        Whether to backup existing file, by default False
    create_dirs : bool, optional
        Whether to create parent directories, by default True

    Returns
    -------
    OperationResult
        OperationResult with write operation details
    """
    errors: list[str] = []
    warnings: list[str] = []
    data: dict[str, Any] = {
        "file_path": str(file_path),
        "encoding": encoding,
        "backup": backup,
        "content_size": len(content),
    }

    try:
        # Create backup if requested and file exists
        if backup and file_path.exists():
            backup_suffix = "pre_write"
            timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            backup_path = file_path.with_suffix(f".{timestamp}_{backup_suffix}.bak")
            shutil.copy2(file_path, backup_path)
            data["backup_path"] = str(backup_path)

        # Create parent directories if requested
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_text(content, encoding=encoding)

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="File written successfully",
            data=data,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Write error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.SYSTEM_ERROR,
            message="File write failed",
            data=data,
            errors=errors,
            warnings=warnings,
        )


def save_yaml_file(
    file_path: pathlib.Path,
    data: dict[str, Any],
    backup: bool = False,
    create_dirs: bool = True,
) -> OperationResult:
    """
    Safely write YAML data to a file with error handling.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to YAML file to write
    data : dict[str, Any]
        Data to serialize as YAML
    backup : bool, optional
        Whether to backup existing file, by default False
    create_dirs : bool, optional
        Whether to create parent directories, by default True

    Returns
    -------
    OperationResult
        OperationResult with write operation details
    """
    errors: list[str] = []
    warnings: list[str] = []
    result_data: dict[str, Any] = {
        "file_path": str(file_path),
        "backup": backup,
        "data_keys": list(data.keys()) if isinstance(data, dict) else "non-dict",
    }

    try:
        # Create backup if requested and file exists
        if backup and file_path.exists():
            backup_suffix = "pre_write"
            timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            backup_path = file_path.with_suffix(f".{timestamp}_{backup_suffix}.bak")
            shutil.copy2(file_path, backup_path)
            result_data["backup_path"] = str(backup_path)

        # Create parent directories if requested
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML file
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="YAML file written successfully",
            data=result_data,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"YAML write error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.SYSTEM_ERROR,
            message="YAML file write failed",
            data=result_data,
            errors=errors,
            warnings=warnings,
        )


def load_yaml_file(file_path: pathlib.Path) -> OperationResult:
    """
    Safely load YAML data from a file with error handling.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to YAML file to load

    Returns
    -------
    OperationResult
        OperationResult with YAML data in data['yaml_data']
    """
    errors: list[str] = []
    warnings: list[str] = []
    data: dict[str, Any] = {"file_path": str(file_path)}

    try:
        if not file_path.exists():
            errors.append(f"YAML file not found: {file_path}")
            return OperationResult(
                success=False,
                exit_code=ExitCode.SYSTEM_ERROR,
                message="YAML file not found",
                data=data,
                errors=errors,
                warnings=warnings,
            )

        if not file_path.is_file():
            errors.append(f"Path is not a file: {file_path}")
            return OperationResult(
                success=False,
                exit_code=ExitCode.SYSTEM_ERROR,
                message="Path is not a file",
                data=data,
                errors=errors,
                warnings=warnings,
            )

        # Load YAML content
        with open(file_path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}

        data["yaml_data"] = yaml_data
        data["data_keys"] = list(yaml_data.keys()) if isinstance(yaml_data, dict) else "non-dict"

        return OperationResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="YAML file loaded successfully",
            data=data,
            errors=errors,
            warnings=warnings,
        )

    except yaml.YAMLError as e:
        errors.append(f"YAML parsing error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.VALIDATION_ERROR,
            message="YAML parsing failed",
            data=data,
            errors=errors,
            warnings=warnings,
        )
    except Exception as e:
        errors.append(f"Load error: {e}")
        return OperationResult(
            success=False,
            exit_code=ExitCode.SYSTEM_ERROR,
            message="YAML file load failed",
            data=data,
            errors=errors,
            warnings=warnings,
        )


# =============================================================================
# Safety and Validation Functions
# =============================================================================


def verify_operation_safety(
    operation: str, target_files: list[pathlib.Path], dry_run: bool = True
) -> ValidationResult:
    """
    Verify that an operation is safe to perform.

    Parameters
    ----------
    operation : str
        Description of operation
    target_files : list[pathlib.Path]
        Files that will be affected
    dry_run : bool, optional
        Whether this is a dry run, by default True

    Returns
    -------
    ValidationResult
        ValidationResult with safety assessment
    """
    errors: list[str] = []
    warnings: list[str] = []
    context: dict[str, Any] = {
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

    # Git repository checks - inline implementation to avoid circular imports
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
        )
        has_uncommitted = result.returncode == 0 and len(result.stdout.strip()) > 0
        if has_uncommitted:
            warnings.append("Working directory has uncommitted changes")
    except Exception:
        # Git not available or other error - not critical for safety check
        pass

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )


def _check_python_version(errors: list[str], context: dict[str, Any]) -> None:
    """Check Python version requirements."""
    python_version = sys.version_info
    context["python_version"] = (
        f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version < (3, 8):
        errors.append(f"Python 3.8+ required, found {context['python_version']}")


def _check_required_directories(errors: list[str]) -> None:
    """Check that required directories exist."""
    required_dirs = [ROOT / "docs", ROOT / "scripts" / "dev"]
    for dir_path in required_dirs:
        if not dir_path.exists():
            errors.append(f"Required directory missing: {dir_path}")


def _check_git_availability(warnings: list[str], context: dict[str, Any]) -> bool:
    """Check git availability and repository status."""
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, check=False, cwd=ROOT
        )
        git_available = result.returncode == 0
    except Exception:
        git_available = False

    context["git_available"] = git_available
    if not git_available:
        warnings.append("Git not available - some features may not work")
        return False

    # Check if we're in a git repository
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
        )
        is_repo = result.returncode == 0
    except Exception:
        is_repo = False

    context["is_git_repo"] = is_repo
    if not is_repo:
        warnings.append("Not in a git repository - some features may not work")

    return git_available


def _check_disk_space(warnings: list[str], context: dict[str, Any]) -> None:
    """Check available disk space."""
    try:
        stat = shutil.disk_usage(ROOT)
        free_space_mb = stat.free // (1024 * 1024)
        context["free_space_mb"] = free_space_mb

        if free_space_mb < 100:  # Less than 100MB
            warnings.append(f"Low disk space: {free_space_mb}MB available")
    except Exception as e:
        warnings.append(f"Could not check disk space: {e}")


def validate_system_prerequisites() -> ValidationResult:
    """
    Validate that all prerequisites for file operations are met.

    Returns
    -------
    ValidationResult
        ValidationResult with prerequisite check results
    """
    errors: list[str] = []
    warnings: list[str] = []
    context: dict[str, Any] = {}

    _check_python_version(errors, context)
    _check_required_directories(errors)
    _check_git_availability(warnings, context)
    _check_disk_space(warnings, context)

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )


def check_file_integrity(file_path: pathlib.Path) -> ValidationResult:
    """
    Check file integrity and accessibility.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to file to check

    Returns
    -------
    ValidationResult
        ValidationResult with integrity check results
    """
    errors: list[str] = []
    warnings: list[str] = []
    context: dict[str, Any] = {"file_path": str(file_path)}

    try:
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return ValidationResult(False, errors, warnings, context)

        if not file_path.is_file():
            errors.append(f"Path is not a file: {file_path}")
            return ValidationResult(False, errors, warnings, context)

        # Check permissions
        if not os.access(file_path, os.R_OK):
            errors.append(f"File is not readable: {file_path}")

        if not os.access(file_path, os.W_OK):
            warnings.append(f"File is not writable: {file_path}")

        # Get file info
        stat = file_path.stat()
        context.update(
            {
                "size": stat.st_size,
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
            }
        )

        # Check if file is empty
        if stat.st_size == 0:
            warnings.append("File is empty")

    except Exception as e:
        errors.append(f"Error checking file integrity: {e}")

    return ValidationResult(
        is_valid=len(errors) == 0, errors=errors, warnings=warnings, context=context
    )
