#!/usr/bin/env python3
"""
Git integration utilities for task automation system.

This module provides git-related functionality extracted from the original
monolithic task_utils.py, including command execution, repository information
gathering, and branch management.

Key Features:
- Safe git command execution with error handling
- Comprehensive repository status checking
- Branch and commit information retrieval
- User configuration validation
- Working directory status monitoring
"""

from __future__ import annotations

import pathlib
import subprocess
from typing import Any

# Get the repository root path
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def run_git_command(cmd: list[str]) -> tuple[bool, str, str]:
    """
    Run a git command safely and return results.

    This function executes git commands in a controlled manner, capturing
    both stdout and stderr while handling exceptions gracefully.

    Parameters
    ----------
    cmd : list[str]
        Git command as list of strings (without the 'git' prefix).
        Example: ['status', '--porcelain'] for 'git status --porcelain'

    Returns
    -------
    tuple[bool, str, str]
        Tuple containing:
        - success (bool): True if command succeeded (returncode == 0)
        - stdout (str): Command stdout, stripped of whitespace
        - stderr (str): Command stderr, stripped of whitespace

    Examples
    --------
    Check git version:
    >>> success, version, error = run_git_command(['--version'])
    >>> if success:
    ...     print(f"Git version: {version}")

    Get current branch:
    >>> success, branch, _ = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
    >>> if success:
    ...     print(f"Current branch: {branch}")
    """
    try:
        result = subprocess.run(
            ["git"] + cmd, capture_output=True, text=True, check=False, cwd=ROOT
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def get_git_info() -> dict[str, Any]:
    """
    Get comprehensive git repository information.

    Gathers various pieces of information about the current git repository
    including branch, commit, user configuration, and working directory status.

    Returns
    -------
    dict[str, Any]
        Dictionary containing git repository information:
        - branch (str): Current branch name or "unknown"
        - commit (str): Short commit hash (8 chars) or "unknown"
        - user_name (str): Git user name or "unknown"
        - user_email (str): Git user email or "unknown"
        - is_clean (bool): True if working directory is clean
        - has_uncommitted (bool): True if there are uncommitted changes

    Examples
    --------
    >>> git_info = get_git_info()
    >>> print(f"Branch: {git_info['branch']}")
    >>> print(f"Commit: {git_info['commit']}")
    >>> if git_info['has_uncommitted']:
    ...     print("Warning: Uncommitted changes detected")
    """
    info: dict[str, Any] = {
        "branch": "unknown",
        "commit": "unknown",
        "user_name": "unknown",
        "user_email": "unknown",
        "is_clean": False,
        "has_uncommitted": False,
    }

    # Get current branch name
    success, branch, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if success:
        info["branch"] = branch

    # Get current commit hash (short form)
    success, commit, _ = run_git_command(["rev-parse", "HEAD"])
    if success:
        info["commit"] = commit[:8]  # Short hash

    # Get git user name configuration
    success, name, _ = run_git_command(["config", "user.name"])
    if success:
        info["user_name"] = name

    # Get git user email configuration
    success, email, _ = run_git_command(["config", "user.email"])
    if success:
        info["user_email"] = email

    # Check working directory status for uncommitted changes
    success, status, _ = run_git_command(["status", "--porcelain"])
    if success:
        info["is_clean"] = len(status) == 0
        info["has_uncommitted"] = len(status) > 0

    return info


def get_current_branch() -> str:
    """
    Get current git branch name with fallback.

    Retrieves the current branch name using git rev-parse. This is a
    convenience function that provides a fallback value if the branch
    cannot be determined.

    Returns
    -------
    str
        Current branch name, or "unknown-branch" if it cannot be determined.

    Examples
    --------
    >>> branch = get_current_branch()
    >>> print(f"Working on branch: {branch}")
    """
    success, branch, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    return branch if success else "unknown-branch"


def check_git_repository() -> tuple[bool, str]:
    """
    Check if current directory is within a git repository.

    Verifies whether the current working directory is inside a git repository
    by checking for the .git directory.

    Returns
    -------
    tuple[bool, str]
        Tuple containing:
        - is_repo (bool): True if in a git repository
        - message (str): Descriptive message about the status

    Examples
    --------
    >>> is_repo, message = check_git_repository()
    >>> if not is_repo:
    ...     print(f"Git repository check failed: {message}")
    """
    success, _, error = run_git_command(["rev-parse", "--git-dir"])
    if success:
        return True, "Git repository detected"
    else:
        return False, f"Not in a git repository: {error}"


def check_git_availability() -> tuple[bool, str]:
    """
    Check if git is available and functional.

    Tests whether the git command is available in the system PATH and
    can be executed successfully.

    Returns
    -------
    tuple[bool, str]
        Tuple containing:
        - available (bool): True if git is available and functional
        - version_info (str): Git version string or error message

    Examples
    --------
    >>> available, version = check_git_availability()
    >>> if available:
    ...     print(f"Git is available: {version}")
    >>> else:
    ...     print(f"Git not available: {version}")
    """
    success, version, error = run_git_command(["--version"])
    if success:
        return True, version
    else:
        return False, f"Git not available: {error}"


def get_repository_status() -> dict[str, Any]:
    """
    Get comprehensive repository status information.

    Combines git availability, repository detection, and basic repository
    information into a single status report.

    Returns
    -------
    dict[str, Any]
        Dictionary containing comprehensive status:
        - git_available (bool): Whether git command is available
        - is_git_repo (bool): Whether current directory is a git repository
        - git_version (str): Git version string or error message
        - repository_info (dict): Repository information from get_git_info()

    Examples
    --------
    >>> status = get_repository_status()
    >>> if not status['git_available']:
    ...     print("Git is not available on this system")
    >>> elif not status['is_git_repo']:
    ...     print("Current directory is not a git repository")
    >>> else:
    ...     info = status['repository_info']
    ...     print(f"Repository: {info['branch']} @ {info['commit']}")
    """
    # Check git availability
    git_available, version_info = check_git_availability()

    # Check if in repository
    is_repo = False
    repo_info = {}

    if git_available:
        is_repo, _ = check_git_repository()
        if is_repo:
            repo_info = get_git_info()

    return {
        "git_available": git_available,
        "is_git_repo": is_repo,
        "git_version": version_info,
        "repository_info": repo_info,
    }
