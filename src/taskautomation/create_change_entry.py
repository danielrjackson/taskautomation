#!/usr/bin/env python3
"""
Script to create a changelog entry file from command-line arguments.

This script gathers information such as change title, author, branch, version, test coverage,
and generates a changelog entry in the appropriate directory using a template.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import subprocess
import sys
import tomllib
from typing import NamedTuple


class OperationResult(NamedTuple):
    """Result of an operation with success status and details."""

    success: bool
    exit_code: int
    message: str


# Default paths - can be overridden for testing
def get_default_root():
    """Get default root directory."""
    return pathlib.Path(__file__).resolve().parent


def get_paths(root_override=None):
    """Get all file paths, with optional root override for testing."""
    root = pathlib.Path(root_override) if root_override else get_default_root()
    return {
        "ROOT": root,
        "TEMPLATE": root / "docs" / "templates" / "changelog" / "template.md",
        "CHANGELOG_DIR": root / "docs" / "changelog",
        "TASKS_MD": root / "docs" / "TASKS.md",
        "PYPROJECT": root / "pyproject.toml",
    }


# Default paths for backward compatibility
_DEFAULT_PATHS = get_paths()
ROOT = _DEFAULT_PATHS["ROOT"]
TEMPLATE = _DEFAULT_PATHS["TEMPLATE"]
CHANGELOG_DIR = _DEFAULT_PATHS["CHANGELOG_DIR"]
TASKS_MD = _DEFAULT_PATHS["TASKS_MD"]
PYPROJECT = _DEFAULT_PATHS["PYPROJECT"]

# ------------------------------------------------------------------------------------------------ #


def run(
    cmd: str | list[str],
    *,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """
    Execute a shell command and return the completed process.

    Parameters
    ----------
        cmd : str | list[str]
            The command to execute, either as a string or a list of arguments.


        check : bool, optional
            If True, raises a CalledProcessError if the command exits with a non-zero status.
            Defaults to False.

    Returns
    -------
        subprocess.CompletedProcess: The result of the executed command, including output and return
        code.
    """
    if isinstance(cmd, str):
        cmd = cmd.split()
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def git(
    cfg_key: str,
    default: str = "",
) -> str:
    """
    Retrieve a git configuration value by key.

    Parameters
    ----------
    cfg_key : str
        The git configuration key to retrieve.
    default : str, optional
        The default value to return if the key is not found (default is "").

    Returns
    -------
    str
        The value of the git configuration key, or the default if not found.
    """
    try:
        return run(["git", "config", "--get", cfg_key], check=True).stdout.strip()
    except subprocess.CalledProcessError:
        return default


def branch() -> str:
    """
    Retrieve the current git branch name, replacing slashes with hyphens.

    Returns
    -------
    str
        The current branch name, or "unknown-branch" if it cannot be determined.
    """
    try:
        return run("git rev-parse --abbrev-ref HEAD", check=True).stdout.strip().replace("/", "-")
    except subprocess.CalledProcessError:
        return "unknown-branch"


def get_version(pyproject_path=None) -> tuple[str, str]:
    """
    Retrieve the project version from the pyproject.toml file.

    Parameters
    ----------
    pyproject_path : str | pathlib.Path | None
        Path to pyproject.toml file. If None, uses default PYPROJECT constant.

    Returns
    -------
        tuple[str, str]
            A tuple containing the version string (e.g., "1.2.3") and a variant with dots replaced
            by hyphens (e.g., "1-2-3"). If the version cannot be determined,
            returns ("0.0.0", "0-0-0").
    """
    pyproject_file = pathlib.Path(pyproject_path) if pyproject_path else PYPROJECT
    try:
        v = tomllib.loads(pyproject_file.read_text())["project"]["version"]
    except (FileNotFoundError, tomllib.TOMLDecodeError, KeyError) as e:
        print(f"Warning: Could not read version from pyproject.toml: {e}", file=sys.stderr)
        v = "0.0.0"
    return v, v.replace(".", "-")


def version(root_override=None) -> OperationResult:
    """
    Get project version with configurable root path - returns OperationResult for testing.

    Parameters
    ----------
    root_override : str | pathlib.Path | None
        Override root directory for testing.

    Returns
    -------
    OperationResult
        Result with version information in message.
    """
    try:
        paths = get_paths(root_override)
        pyproject_file = paths["PYPROJECT"]

        if not pyproject_file.exists():
            return OperationResult(
                success=False, exit_code=1, message=f"pyproject.toml not found: {pyproject_file}"
            )

        ver, ver_slug = get_version(pyproject_file)
        return OperationResult(
            success=True, exit_code=0, message=f"Version: {ver} (slug: {ver_slug})"
        )
    except Exception as e:
        return OperationResult(success=False, exit_code=1, message=f"Error getting version: {e}")


def utc_slug() -> str:
    """
    Generate a UTC timestamp slug in the format YYYYMMDDTHHMMSSZ.

    Returns
    -------
    str
        The current UTC time as a string slug.
    """
    return _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def get_first_task(tasks_md_path=None) -> str | None:
    """
    Retrieve the first unchecked task from the TASKS.md file.

    Parameters
    ----------
    tasks_md_path : str | pathlib.Path | None
        Path to TASKS.md file. If None, uses default TASKS_MD constant.

    Returns
    -------
    str | None
        The description of the first unchecked task, or None if not found or file does not exist.
    """
    tasks_file = pathlib.Path(tasks_md_path) if tasks_md_path else TASKS_MD
    if not tasks_file.exists():
        return None
    m = re.search(r"^- \[ \] \*\*(.+?)\*\*:", tasks_file.read_text(), re.M)
    return m.group(1) if m else None


def first_task(root_override=None) -> OperationResult:
    """
    Get first unchecked task with configurable root path - returns OperationResult for testing.

    Parameters
    ----------
    root_override : str | pathlib.Path | None
        Override root directory for testing.

    Returns
    -------
    OperationResult
        Result with first task information in message.
    """
    try:
        paths = get_paths(root_override)
        tasks_file = paths["TASKS_MD"]

        if not tasks_file.exists():
            return OperationResult(
                success=False, exit_code=1, message=f"TASKS.md not found: {tasks_file}"
            )

        task = get_first_task(tasks_file)
        if task:
            return OperationResult(success=True, exit_code=0, message=f"First task: {task}")
        else:
            return OperationResult(success=True, exit_code=0, message="No unchecked tasks found")
    except Exception as e:
        return OperationResult(success=False, exit_code=1, message=f"Error getting first task: {e}")


# --------------------------------------------------------------------------- #
COV_LINE = re.compile(r"^TOTAL\s+\d+\s+\d+\s+\d+\s+(\d+)%", re.M)
FAIL_LINE = re.compile(r"^FAILED .+", re.M)


def run_tests(cmd: str) -> tuple[str | None, list[str]]:
    """
    Run the test command and extract coverage percentage and failure lines.

    Parameters
    ----------
    cmd : str
        The command to run tests (e.g., pytest with coverage).

    Returns
    -------
    tuple[str | None, list[str]]
        A tuple containing the coverage percentage as a string (or None if tests failed)
        and a list of failure lines (empty if tests passed).

    """
    cp = run(cmd, check=False)
    if cp.returncode == 0:
        m = COV_LINE.search(cp.stdout)
        alt = re.search(r"coverage:\s+(\d+(?:\.\d+)?)% of", cp.stdout)
        pct = m.group(1) if m else (alt.group(1) if alt else "")
        return pct, []
    # tests failed
    fails = FAIL_LINE.findall(cp.stdout)
    if not fails:
        fails = ["Tests failed (see log)"]
    return None, fails


def render(raw: str, **kw) -> str:
    """
    Render a template string using the provided keyword arguments.

    Parameters
    ----------
    raw : str
        The template string to render.
    **kw
        Keyword arguments to substitute into the template.

    Returns
    -------
    str
        The rendered string with placeholders replaced by keyword arguments.

    """
    return raw.format_map({k: v or "" for k, v in kw.items()})


# --------------------------------------------------------------------------- #
def main(argv=None, root_override=None):
    """
    Create a changelog entry file from command-line arguments.

    Parameters
    ----------
    argv : list[str] or None
        Command-line arguments to parse (default: None, uses sys.argv).
    root_override : str | pathlib.Path | None
        Override root directory for testing. If None, uses default paths.

    Returns
    -------
    None

    """
    # Get configurable paths
    paths = get_paths(root_override)
    template = paths["TEMPLATE"]
    changelog_dir = paths["CHANGELOG_DIR"]
    tasks_md = paths["TASKS_MD"]
    pyproject = paths["PYPROJECT"]
    root = paths["ROOT"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--change-title")
    ap.add_argument("--author-name")
    ap.add_argument("--author-contact-url")
    ap.add_argument("--change-type")
    ap.add_argument("--issue-number", type=int)
    ap.add_argument("--coverage-percentage")
    ap.add_argument("--test-cmd", default="pytest -q --cov --cov-report=term")
    ap.add_argument("--skip-coverage", action="store_true")
    args = ap.parse_args(argv)

    br, (ver, vslug), dt = branch(), get_version(pyproject), utc_slug()

    # run tests (unless skipped or cov supplied)
    coverage, fail_lines = (
        (args.coverage_percentage, [])
        if (args.skip_coverage or args.coverage_percentage)
        else run_tests(args.test_cmd)
    )

    # assemble description
    desc = ""
    if fail_lines:
        bullet = "\n          ".join(fail_lines)
        desc = f"- [ ] **Fix failing tests**\n          {bullet}"
    else:
        task = get_first_task(tasks_md)
        if task:
            desc = f"Addresses task: {task}"

    # author autodetect
    author = args.author_name or git("user.name")
    contact = args.author_contact_url or (
        f"mailto:{git('user.email')}" if git("user.email") else ""
    )

    fields = dict(
        change_title=args.change_title or "Untitled Change",
        author_name=author,
        author_contact_url=contact,
        branch_name=br,
        version=ver,
        version_slug=vslug,
        date_time=dt,
        change_type=args.change_type or "",
        issue_number=args.issue_number or "",
        coverage_percentage=coverage or "",
        description=desc,
    )

    # Check if template file exists
    if not template.exists():
        print(f"Error: Template file not found: {template}", file=sys.stderr)
        sys.exit(1)

    changelog_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{br}_{vslug}_{dt}.md"
    out = changelog_dir / fname
    out.write_text(render(template.read_text(), **fields))
    print(out.relative_to(root))  # required output


if __name__ == "__main__":
    main()
