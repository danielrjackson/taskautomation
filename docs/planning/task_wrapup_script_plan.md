# Task Wrap-up Script Implementation Plan

## Objective

Create `scripts/dev/finish_tasks.py` - a script that wraps up completed tasks by:

1. Finding tasks marked as complete but missing finish times
2. Adding finish timestamps to those tasks  
3. Moving completed tasks to the Archive section
4. Generating a list of finished tasks for change entry files and git commit messages

## Script Design: `scripts/dev/finish_tasks.py`

### Single Purpose

Wrap up completed tasks and prepare them for change entry generation and git commits.

### CLI Interface

```bash
# Find and finish all completed tasks missing finish times
python scripts/dev/finish_tasks.py

# Finish specific tasks by ID
python scripts/dev/finish_tasks.py --task-ids 4,5,6

# Interactive mode - show completed tasks and let user select
python scripts/dev/finish_tasks.py --interactive

# Only update finish times, don't archive yet
python scripts/dev/finish_tasks.py --timestamps-only
```

### "Check Your Work" Features

```bash
# Preview what would be finished without making changes
python scripts/dev/finish_tasks.py --dry-run

# List completed tasks missing finish times
python scripts/dev/finish_tasks.py --list-incomplete

# Show current archive statistics
python scripts/dev/finish_tasks.py --archive-stats
```

## Core Functionality

### 1. Task Detection Logic

```python
def find_completed_tasks_needing_finish():
    """
    Find tasks that are:
    - Marked as completed (checkbox checked: [x])
    - Missing finish timestamps (Finish Date: None)
    - Not already in Archive section
    """
    # Parse TASKS.md using patterns from run_tests.py
    # Return list of TaskInfo objects needing finish times
```

### 2. Timestamp Addition

```python
def add_finish_timestamps(task_ids: list[int], timestamp: str = None):
    """
    Add finish timestamps to specified tasks
    - Use current ISO8601 timestamp if not provided
    - Update task in-place in TASKS.md
    - Preserve all other task metadata
    """
    # Follow the pattern established in run_tests.py for task updates
```

### 3. Archive Management  

```python
def archive_completed_tasks(task_ids: list[int]):
    """
    Move completed tasks from priority sections to Archive
    - Extract complete task blocks
    - Remove from current location
    - Add to Archive section with completion timestamp
    - Maintain task formatting and metadata
    """
```

### 4. Change Entry Preparation

```python
def generate_finished_tasks_summary(task_ids: list[int]) -> dict:
    """
    Generate summary of finished tasks for change entries and commits
    Returns:
    {
        'task_list': ['Task 4: Fix authentication bug', 'Task 5: Add validation'],
        'task_ids': [4, 5],
        'commit_message_snippet': 'Completed tasks #4, #5',
        'change_entry_items': ['- Fixed authentication bug (Task #4)', '- Added validation (Task #5)']
    }
    """
```

## Integration with Existing Scripts

### Calls Existing Scripts

```python
# Use existing create_change_entry.py for change file generation
def create_change_entries_for_tasks(task_summary: dict):
    """Call existing create_change_entry.py with task information"""
    
# Use task parsing patterns directly from run_tests.py
# Extract shared utilities if needed for reuse
```

### Output Format

The script outputs structured information that can be used by other scripts:

```bash
$ python scripts/dev/finish_tasks.py --task-ids 4,5

✓ Updated finish times for 2 tasks
✓ Archived 2 completed tasks  
✓ Generated change entry summary

Finished Tasks:
- Task #4: Fix failing tests in tests/test_example_module.py
- Task #5: Create Tasks

For Change Entry:
- Fixed 3 failing tests in tests/test_example_module.py (Task #4)  
- Created initial task structure for project (Task #5)

For Git Commit:
feat: Complete authentication and task management work

Addresses tasks #4, #5:
- Fixed failing tests in test_example_module.py
- Created initial task structure and documentation

Change entry file: docs/changelog/main_0-1-0_20250730T124523Z.md
```

## Implementation Details

### Task Parsing (Based on run_tests.py patterns)

```python
# Use the same regex patterns from run_tests.py for consistency
TASK_BLOCK_RE = re.compile(r"- \[([ x])\] \*\*(.+?)\*\*:", re.M)
ID_RE = re.compile(r"- \*\*ID\*\*: (\d+)", re.M)
FINISH_DATE_RE = re.compile(r"- \*\*Finish Date\*\*: (.+)", re.M)

class TaskInfo(NamedTuple):
    task_id: int
    title: str
    checked: bool
    finish_date: str | None
    priority: str
    # ... use same fields as run_tests.py TaskInfo
```

### Archive Section Management

```python
def ensure_archive_section_exists(content: str) -> str:
    """Ensure TASKS.md has an Archive section"""
    if "## Archive" not in content:
        # Add archive section before the final separator
        # Follow existing TASKS.md structure
    return content

def add_to_archive(task_block: str, content: str) -> str:
    """Add completed task block to Archive section"""
    # Insert task block in Archive section
    # Maintain chronological order by finish date
```

### Error Handling & Validation

```python
def validate_task_for_finishing(task_id: int) -> bool:
    """
    Validate task can be finished:
    - Task exists
    - Task is marked complete ([x])
    - Task is not already in Archive
    - Task has valid metadata
    """

def backup_tasks_file():
    """Create backup of TASKS.md before modifications"""
    # Safety measure for automation
```

## Example Usage Scenarios

### Scenario 1: Daily Wrap-up

```bash
# At end of day, finish all completed work
python scripts/dev/finish_tasks.py --dry-run    # Check what would be finished
python scripts/dev/finish_tasks.py              # Actually finish the tasks
```

### Scenario 2: Preparing for Commit

```bash
# Before creating a commit, wrap up specific tasks
python scripts/dev/finish_tasks.py --task-ids 4,5 > task_summary.txt
# Use task_summary.txt for commit message and change entry
```

### Scenario 3: Interactive Task Management

```bash
# Interactive session to select tasks to finish
python scripts/dev/finish_tasks.py --interactive
# Script shows completed tasks and lets user select which to finish/archive
```

## Testing Strategy

### Unit Tests

- Test task detection logic with sample TASKS.md content
- Test timestamp addition and formatting
- Test archive section management
- Test change entry summary generation

### Integration Tests  

- Test with actual TASKS.md structure
- Test integration with create_change_entry.py
- Test error handling and recovery scenarios

### Manual Testing

- Test with various task states and priorities
- Test edge cases (no completed tasks, malformed tasks, etc.)
- Test backup and recovery functionality

## Success Criteria

### Functionality

- ✅ Correctly identifies completed tasks missing finish times
- ✅ Adds accurate ISO8601 timestamps
- ✅ Moves tasks to Archive section without losing data
- ✅ Generates useful summary for change entries and commits
- ✅ Integrates cleanly with existing scripts

### Usability  

- ✅ Clear "check your work" dry-run mode
- ✅ Helpful error messages and validation
- ✅ Consistent CLI interface with other scripts
- ✅ Safe operation with backup capabilities

### Integration

- ✅ Works with existing TASKS.md format
- ✅ Calls existing create_change_entry.py appropriately  
- ✅ Provides output suitable for git commit messages
- ✅ Maintains consistency with run_tests.py patterns

This script will be the foundation for automating the task completion workflow while maintaining the modular, single-purpose approach you wanted.
