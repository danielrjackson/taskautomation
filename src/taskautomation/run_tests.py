#!/usr/bin/env python3
"""
Enhanced test runner script with task management and coverage reporting.

Features:
- Runs pytest with coverage reporting by default
- Manages test-related tasks in `docs/TASKS.md` with priority sections
- Updates existing open tasks by checking off passing tests and adding new failing tests
- Only modifies open tasks, leaves completed tasks unchanged
- Each test file gets its own task, each test gets its own subtask with checkbox
- Report-only mode shows what would be changed without updating the file
- Forwards unrecognized arguments directly to pytest
- Configurable coverage reporting (html, terminal, none)
- Quiet mode to suppress extra output
- Assigns tasks to "Roo" when doing work
- Organizes tasks by priority with archive section for completed tasks

Usage:
    python run_tests.py [OPTIONS] [-- PYTEST_ARGS]

Options:
    --update-tasks       Actually update TASKS.md (default: report-only mode)
    --quiet             Suppress extra output
    --coverage MODE     Coverage reporting mode: html, terminal, none (default: terminal)
    -- PYTEST_ARGS     Arguments to forward directly to pytest

Examples:
    python run_tests.py                              # Report mode with terminal coverage
    python run_tests.py --update-tasks               # Update TASKS.md with terminal coverage
    python run_tests.py --coverage html              # Report mode with HTML coverage
    python run_tests.py --quiet --update-tasks       # Update TASKS.md quietly
    python run_tests.py -- -v -x                     # Forward -v -x to pytest
"""

from __future__ import annotations

# Standard Library
import argparse
import collections
import datetime
import pathlib
import re
import subprocess
import sys
import textwrap
from typing import NamedTuple


# Default paths - can be overridden for testing
def get_default_root():
    """Get default root directory."""
    return pathlib.Path(__file__).resolve().parent.parent.parent


def get_paths(root_override=None):
    """Get all file paths, with optional root override for testing."""
    root = pathlib.Path(root_override) if root_override else get_default_root()
    return {"ROOT": root, "TASKS": root / "docs" / "TASKS.md"}


# Default paths for backward compatibility
_DEFAULT_PATHS = get_paths()
ROOT = _DEFAULT_PATHS["ROOT"]
TASKS = _DEFAULT_PATHS["TASKS"]

# Regex patterns for parsing pytest output
FAIL_RE = re.compile(r"^(.+?)::(.+?) FAILED", re.M)  # capture file path and test name
PASS_RE = re.compile(r"^(.+?)::(.+?) PASSED", re.M)  # capture file path and test name
SHORT_FAIL_RE = re.compile(r"^FAILED (.+?)::", re.M)  # fallback for file path only

# Regex patterns for parsing TASKS.md
TASK_BLOCK_RE = re.compile(r"- \[([ x])\] \*\*Fix failing tests in (.+?)\*\*:", re.M)
SUBTASK_RE = re.compile(r"    - \[([ x])\] (.+?)(?:\n|$)", re.M)
ID_RE = re.compile(r"- \*\*ID\*\*: (\d+)", re.M)
PRIORITY_SECTION_RE = re.compile(r"^## (.+) Priority Tasks?$", re.M)
ARCHIVE_SECTION_RE = re.compile(r"^## Archive$", re.M)


class TestResult(NamedTuple):
    """Represents the result of a single test."""  # noqa: D203

    file_path: str
    test_name: str
    status: str  # 'PASSED' or 'FAILED'


class TaskInfo(NamedTuple):
    """Represents a test-related task in TASKS.md."""  # noqa: D203

    file_path: str
    checked: bool
    task_id: int
    priority: str
    assignee: str | None
    create_date: str | None
    start_date: str | None
    finish_date: str | None
    subtasks: dict[str, bool]  # test_name -> checked


def run(cmd: str) -> tuple[int, str]:
    """
    Execute a shell command and return its exit code along with combined output.

    Parameters
    ----------
    cmd : str
        The shell command to execute.

    Returns
    -------
    tuple[int, str]
        Tuple of (exit_code, combined_stdout_stderr)
    """
    cp = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return cp.returncode, (cp.stdout or "") + (cp.stderr or "")


def parse_test_results(output: str) -> list[TestResult]:
    """
    Parse pytest output to extract individual test results.

    Parameters
    ----------
    output : str
        Combined stdout/stderr from pytest

    Returns
    -------
    list[TestResult]
        List of TestResult objects
    """
    results = []

    # Parse FAILED tests
    for match in FAIL_RE.finditer(output):
        file_path = match.group(1)
        test_name = match.group(2)
        results.append(TestResult(file_path, test_name, "FAILED"))

    # Parse PASSED tests
    for match in PASS_RE.finditer(output):
        file_path = match.group(1)
        test_name = match.group(2)
        results.append(TestResult(file_path, test_name, "PASSED"))

    return results


def group_results_by_file(results: list[TestResult]) -> dict[str, dict[str, str]]:
    """
    Group test results by file path.

    Parameters
    ----------
    results : list[TestResult]
        List of TestResult objects

    Returns
    -------
    dict[str, dict[str, str]]
        Dict mapping file_path -> {test_name: status}
    """
    by_file: dict[str, dict[str, str]] = collections.defaultdict(dict)
    for result in results:
        by_file[result.file_path][result.test_name] = result.status
    return by_file


def parse_existing_tasks(task_text: str) -> dict[str, TaskInfo]:  # noqa: C901
    """
    Parse existing test-related tasks from TASKS.md.

    Parameters
    ----------
    task_text : str
        Content of TASKS.md file

    Returns
    -------
    dict[str, TaskInfo]
        Dict mapping file_path -> TaskInfo
    """
    tasks = {}
    lines = task_text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]
        task_match = TASK_BLOCK_RE.match(line)

        if task_match:
            checked = task_match.group(1) == "x"
            file_path = task_match.group(2)
            subtasks = {}
            task_id = -1
            priority = "Critical"
            assignee = None
            create_date = None
            start_date = None
            finish_date = None

            # Look for task metadata and subtasks in following lines
            i += 1
            in_subtasks_section = False
            while i < len(lines):
                line = lines[i]

                # Parse task metadata
                if line.strip().startswith("- **ID**: "):
                    try:
                        task_id = int(line.split(": ")[1])
                    except (ValueError, IndexError):
                        task_id = -1
                elif line.strip().startswith("- **Priority**: "):
                    priority = line.split(": ")[1].strip()
                elif line.strip().startswith("- **Assignee**: "):
                    assignee_val = line.split(": ")[1].strip()
                    assignee = assignee_val if assignee_val != "None" else None
                elif line.strip().startswith("- **Create Date**: "):
                    create_date_val = line.split(": ")[1].strip()
                    create_date = create_date_val if create_date_val != "None" else None
                elif line.strip().startswith("- **Start Date**: "):
                    start_date_val = line.split(": ")[1].strip()
                    start_date = start_date_val if start_date_val != "None" else None
                elif line.strip().startswith("- **Finish Date**: "):
                    finish_date_val = line.split(": ")[1].strip()
                    finish_date = finish_date_val if finish_date_val != "None" else None
                elif line.strip().startswith("- **Subtasks**:"):
                    in_subtasks_section = True
                elif in_subtasks_section and line.startswith("    - ["):
                    subtask_match = SUBTASK_RE.match(line)
                    if subtask_match:
                        sub_checked = subtask_match.group(1) == "x"
                        test_name = subtask_match.group(2).replace(
                            "Fix ", ""
                        )  # Remove "Fix " prefix
                        subtasks[test_name] = sub_checked
                elif line.strip() == "" or line.startswith("- ["):
                    # Empty line or new task
                    break
                i += 1

            # Only add tasks that are NOT completed (checked)
            if not checked:
                tasks[file_path] = TaskInfo(
                    file_path,
                    checked,
                    task_id,
                    priority,
                    assignee,
                    create_date,
                    start_date,
                    finish_date,
                    subtasks,
                )
            continue

        i += 1

    return tasks


def get_next_task_id(task_text: str) -> int:
    """
    Get the next available task ID by finding the largest existing ID and incrementing.

    Parameters
    ----------
    task_text : str
        Content of TASKS.md file

    Returns
    -------
    int
        Next available task ID
    """
    max_id = 0
    for match in ID_RE.finditer(task_text):
        try:
            task_id = int(match.group(1))
            if task_id > max_id:
                max_id = task_id
        except ValueError:
            continue
    return max_id + 1


def get_current_datetime() -> str:
    """
    Get current datetime in ISO8601 format.

    Returns
    -------
    str
        Current datetime in ISO8601 format with Z suffix
    """
    return datetime.datetime.now().isoformat() + "Z"


def format_task_block(
    file_path: str,
    test_results: dict[str, str],
    task_id: int,
    existing_subtasks: dict[str, bool] | None = None,
    existing_task: TaskInfo | None = None,
) -> str:
    """
    Format a task block for a test file following the standard task format.

    Parameters
    ----------
    file_path : str
        Path to the test file
    test_results : dict[str, str]
        Dict of test_name -> status for this file
    task_id : int
        ID to assign to this task
    existing_subtasks : dict[str, bool] | None, optional
        Existing subtask completion status
    existing_task : TaskInfo | None, optional
        Existing task info if updating

    Returns
    -------
    str
        Formatted task block string
    """
    if existing_subtasks is None:
        existing_subtasks = {}

    # Determine if main task should be checked (all tests passing)
    has_failures = any(status == "FAILED" for status in test_results.values())
    main_checked = "[ ]" if has_failures else "[x]"

    # Count failing tests for description
    failing_count = sum(1 for status in test_results.values() if status == "FAILED")

    # Determine dates and assignee
    current_datetime = get_current_datetime()

    if existing_task:
        # Updating existing task
        create_date = existing_task.create_date or current_datetime
        start_date = existing_task.start_date or current_datetime
        finish_date = current_datetime if main_checked == "[x]" else existing_task.finish_date
        assignee = existing_task.assignee or "Roo"
        priority = existing_task.priority
    else:
        # New task
        create_date = current_datetime
        start_date = current_datetime
        finish_date = current_datetime if main_checked == "[x]" else None
        assignee = "Roo"
        priority = "Critical"

    lines = [
        f"- {main_checked} **Fix failing tests in {file_path}**:",
        f"  - **ID**: {task_id}",
        f"  - **Description**: Fix {failing_count} failing test"
        f"{'s' if failing_count != 1 else ''} in {file_path}",
        "  - **Pre-requisites**:",
        "    - None",
        f"  - **Priority**: {priority}",
        "  - **Estimated Time**: 30 minutes",
        f"  - **Assignee**: {assignee or 'None'}",
        f"  - **Create Date**: {create_date or 'None'}",
        f"  - **Start Date**: {start_date or 'None'}",
        f"  - **Finish Date**: {finish_date or 'None'}",
        "  - **Subtasks**:",
    ]

    # Preserve exact order of existing subtasks, only change checkbox status
    # First, add existing subtasks in their original order
    for test_name, _was_checked in existing_subtasks.items():
        current_status = test_results.get(
            test_name, "PASSED"
        )  # Default to PASSED if not in current results

        if current_status == "FAILED":
            # Still failing - keep unchecked
            checked = "[ ]"
        else:
            # Passing now - check it off
            checked = "[x]"

        lines.append(f"    - {checked} Fix {test_name}")

    # Then, add any new failing tests that weren't in existing subtasks
    for test_name, status in test_results.items():
        if status == "FAILED" and test_name not in existing_subtasks:
            lines.append(f"    - [ ] Fix {test_name}")

    return "\n".join(lines) + "\n"


def generate_report(
    current_results: dict[str, dict[str, str]], existing_tasks: dict[str, TaskInfo]
) -> tuple[list[str], list[str], list[str]]:
    """
    Generate report of test status changes.

    Parameters
    ----------
    current_results : dict[str, dict[str, str]]
        Current test results by file
    existing_tasks : dict[str, TaskInfo]
        Existing tasks from TASKS.md

    Returns
    -------
    tuple[list[str], list[str], list[str]]
        Tuple of (newly_fixed, newly_broken, still_failing)
    """
    newly_fixed = []
    newly_broken = []
    still_failing = []

    # Check each test file's results
    for file_path, test_results in current_results.items():
        existing_task = existing_tasks.get(file_path)

        for test_name, current_status in test_results.items():
            if current_status == "PASSED":
                # Test is currently passing
                if (
                    existing_task
                    and test_name in existing_task.subtasks
                    and not existing_task.subtasks[test_name]
                ):
                    # Was failing, now passing
                    newly_fixed.append(f"{file_path}::{test_name}")
            else:  # FAILED
                # Test is currently failing
                if not existing_task or test_name not in existing_task.subtasks:
                    # New failure
                    newly_broken.append(f"{file_path}::{test_name}")
                else:
                    # Still failing
                    still_failing.append(f"{file_path}::{test_name}")

    return newly_fixed, newly_broken, still_failing


def organize_tasks_by_priority(task_blocks: list[str], original_text: str) -> str:
    """
    Organize tasks into priority sections and add archive section.

    Parameters
    ----------
    task_blocks : list[str]
        List of formatted task blocks
    original_text : str
        Original TASKS.md content

    Returns
    -------
    str
        New organized content with priority sections
    """
    lines = original_text.split("\n")

    # Build the new content (removed unused sections variable)

    # Build the new content
    new_lines = []

    # Find the first dash line (start of tasks section)
    first_dash_line = -1
    for i, line in enumerate(lines):
        if line.startswith("---") and len(line.strip()) > 10:
            first_dash_line = i
            break

    if first_dash_line >= 0:
        # Add everything up to and including the first dash line
        new_lines.extend(lines[: first_dash_line + 1])
    else:
        # No dash lines found, add basic structure
        new_lines = lines[:]
        new_lines.append("")
        new_lines.append("---" + "-" * 90)

    new_lines.append("")

    # Add priority sections with tasks
    priority_order = ["Critical", "High", "Medium", "Low"]

    for priority in priority_order:
        new_lines.append(f"## {priority} Priority Tasks")
        new_lines.append("")

        # Add test task blocks if they match this priority
        for block in task_blocks:
            if f"- **Priority**: {priority}" in block:
                new_lines.extend(block.rstrip().split("\n"))
                new_lines.append("")

        # Add existing non-test tasks for this priority (if any exist)
        # For now, we'll put existing tasks in their original locations
        # This is a placeholder for future enhancement

        new_lines.append("")

    # Add archive section
    new_lines.append("## Archive")
    new_lines.append("")
    new_lines.append("*Completed tasks are moved here for historical reference.*")
    new_lines.append("")

    # Find and add the second dash line if it exists
    second_dash_line = -1
    for i in range(first_dash_line + 1 if first_dash_line >= 0 else 0, len(lines)):
        if lines[i].startswith("---") and len(lines[i].strip()) > 10:
            second_dash_line = i
            break

    if second_dash_line >= 0:
        new_lines.append("---" + "-" * 90)
        new_lines.extend(lines[second_dash_line + 1 :])
    else:
        new_lines.append("---" + "-" * 90)

    return "\n".join(new_lines)


def update_tasks_file(  # noqa: C901
    current_results: dict[str, dict[str, str]],
    existing_tasks: dict[str, TaskInfo],
    dry_run: bool = True,
    tasks_file: pathlib.Path | None = None,
) -> bool:
    """
    Update the TASKS.md file with current test results organized by priority.

    Parameters
    ----------
    current_results : dict[str, dict[str, str]]
        Current test results by file
    existing_tasks : dict[str, TaskInfo]
        Existing tasks from TASKS.md
    dry_run : bool, optional
        If True, don't actually write the file
    tasks_file : pathlib.Path, optional
        Path to tasks file. If None, uses default TASKS constant.

    Returns
    -------
    bool
        True if changes were made (or would be made)
    """
    tasks_path = tasks_file if tasks_file is not None else TASKS
    tasks_path.parent.mkdir(parents=True, exist_ok=True)

    if tasks_path.exists():
        original_text = tasks_path.read_text()
    else:
        original_text = (
            "# taskautomation Task List\n\n## Instructions\n\n"
            "See the [Task Instructions] for detailed instructions on how to "
            "complete tasks for the project.\n\n## Tasks\n\n"
        )

    # Get next task ID
    next_task_id = get_next_task_id(original_text)

    # Start building new content
    new_blocks = []
    has_changes = False
    current_task_id = next_task_id

    # Process files with test results
    for file_path, test_results in current_results.items():
        existing_task = existing_tasks.get(file_path)

        # Only create/update tasks for files with failures OR files that had existing tasks
        has_failures = any(status == "FAILED" for status in test_results.values())
        if not has_failures and not existing_task:
            continue  # Skip files with all passing tests and no existing task

        if existing_task:
            # Update existing task - use existing task ID and info
            existing_subtasks = existing_task.subtasks.copy()
            task_id = existing_task.task_id

            # Check if there are any changes needed
            for test_name, status in test_results.items():
                if status == "FAILED" and test_name not in existing_subtasks:
                    has_changes = True  # New failing test
                elif (
                    status == "PASSED"
                    and test_name in existing_subtasks
                    and not existing_subtasks[test_name]
                ):
                    has_changes = True  # Test now passing
        else:
            # New task needed
            has_changes = True
            existing_subtasks = {}
            task_id = current_task_id
            current_task_id += 1

        new_blocks.append(
            format_task_block(file_path, test_results, task_id, existing_subtasks, existing_task)
        )

    if not has_changes:
        return False

    if not dry_run:
        # Organize tasks by priority sections
        new_content = organize_tasks_by_priority(new_blocks, original_text)
        tasks_path.write_text(new_content)

        # Run ruff formatter on the updated file
        try:
            run("ruff format " + str(tasks_path))
        except Exception:
            pass  # Don't fail if ruff isn't available

    return has_changes


def build_pytest_command(coverage_mode: str, pytest_args: list[str]) -> str:
    """
    Build the pytest command with coverage options.

    Parameters
    ----------
    coverage_mode : str
        'html', 'terminal', or 'none'
    pytest_args : list[str]
        Additional arguments to pass to pytest

    Returns
    -------
    str
        Complete pytest command string
    """
    base_cmd = ["pytest", "-v"]  # Use verbose mode to get individual test results

    if coverage_mode == "html":
        base_cmd.extend(["--cov=taskautomation", "--cov-report=html"])
    elif coverage_mode == "terminal":
        base_cmd.extend(["--cov=taskautomation", "--cov-report=term-missing"])
    # For 'none', don't add coverage options

    base_cmd.extend(pytest_args)
    return " ".join(base_cmd)


def main(argv=None, root_override=None):  # noqa: C901
    """
    Run the enhanced test runner with task management.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command line arguments to parse. If None, uses sys.argv
    root_override : str | pathlib.Path | None, optional
        Override root directory for testing. If None, uses default paths.
    """
    # Get configurable paths
    paths = get_paths(root_override)
    tasks_file = paths["TASKS"]

    parser = argparse.ArgumentParser(
        description="Enhanced test runner with task management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s                              # Report mode with terminal coverage
          %(prog)s --update-tasks               # Update TASKS.md with terminal coverage
          %(prog)s --coverage html              # Report mode with HTML coverage
          %(prog)s --quiet --update-tasks       # Update TASKS.md quietly
          %(prog)s -- -v -x                     # Forward -v -x to pytest
        """),
    )

    parser.add_argument(
        "--update-tasks",
        action="store_true",
        help="Actually update TASKS.md (default: report-only mode)",
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress extra output")

    parser.add_argument(
        "--coverage",
        choices=["html", "terminal", "none"],
        default="terminal",
        help="Coverage reporting mode (default: %(default)s)",
    )

    # Parse known args to separate our options from pytest args
    args, pytest_args = parser.parse_known_args(argv)

    # Build and run pytest command
    test_cmd = build_pytest_command(args.coverage, pytest_args)
    if not args.quiet:
        print(f"Running: {test_cmd}")

    rc, output = run(test_cmd)

    # Parse test results
    test_results = parse_test_results(output)
    current_results = group_results_by_file(test_results)

    # Parse existing tasks
    existing_tasks = {}
    if tasks_file.exists():
        task_text = tasks_file.read_text()
        existing_tasks = parse_existing_tasks(task_text)

    # Generate report
    newly_fixed, newly_broken, still_failing = generate_report(current_results, existing_tasks)

    # Print report unless quiet
    if not args.quiet:
        if newly_fixed:
            print(f"\n✓ Tests fixed since last update ({len(newly_fixed)}):")
            for test in newly_fixed:
                print(f"  - {test}")

        if newly_broken:
            print(f"\n✗ Newly failing tests ({len(newly_broken)}):")
            for test in newly_broken:
                print(f"  - {test}")

        if still_failing:
            print(f"\n⚠ Still failing tests ({len(still_failing)}):")
            for test in still_failing:
                print(f"  - {test}")

        if not newly_fixed and not newly_broken and not still_failing:
            print("\n✓ All tests passing, no task updates needed")

    # Update tasks file
    changes_made = update_tasks_file(
        current_results, existing_tasks, dry_run=not args.update_tasks, tasks_file=tasks_file
    )

    if not args.quiet:
        if args.update_tasks:
            if changes_made:
                print("\n📝 TASKS.md updated")
            else:
                print("\n📝 No changes needed to TASKS.md")
        else:
            if changes_made:
                print("\n📝 TASKS.md would be updated (use --update-tasks to apply)")
            else:
                print("\n📝 No changes would be made to TASKS.md")

    # Exit with appropriate code
    sys.exit(rc)


if __name__ == "__main__":
    main()
