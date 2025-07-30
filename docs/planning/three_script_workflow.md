# Three-Script Workflow Plan

## Overview

Automate the task workflow with three main scripts that handle the automatable "startup/finish up" parts while leaving the creative work manual.

## Workflow: `select_next_task` → **[manual work]** → `finalize_task` → `submit_change`

### 1. `scripts/dev/select_next_task.py`

**Purpose**: Pick next task, run tests to create failing test tasks, create change entry file

**What it does**:

1. **Run tests first** - Uses existing [`run_tests.py`](../../scripts/dev/run_tests.py) to identify failing tests
2. **Auto-create test tasks** - Any failing tests get added as high-priority tasks in TASKS.md
3. **Select highest priority task** - Picks the next task to work on based on priority
4. **Create change entry** - Uses existing [`create_change_entry.py`](../../scripts/dev/create_change_entry.py) to create the changelog file upfront
5. **Mark task as started** - Updates task with start timestamp and assignee

**CLI Interface**:

```bash
# Auto-select next highest priority task
python scripts/dev/select_next_task.py

# Select specific task by ID
python scripts/dev/select_next_task.py --task-id 4

# Preview what would be selected without making changes
python scripts/dev/select_next_task.py --dry-run
```

**AI-Friendly Output** (JSON format):

```json
{
  "success": true,
  "selected_task": {
    "id": 4,
    "title": "Fix failing tests in tests/test_example_module.py",
    "description": "Fix 3 failing tests in tests/test_example_module.py",
    "priority": "Critical",
    "estimated_time": "30 minutes"
  },
  "change_entry_file": "docs/changelog/main_0-1-0_20250730T124523Z.md",
  "test_failures_added": 2,
  "new_tasks_created": [5, 6],
  "ready_to_work": true
}
```

**Output for AI Agent**:

- Path to the change entry file to read for task details
- Task information and context
- Any new test-related tasks that were auto-created

---

### 2. **[Manual Work Phase]**

- AI agent reads the change entry file to understand the task
- Implements the solution (creative work that requires intelligence)
- Can periodically run validation scripts to check progress

**Available during work**:

```bash
# Check current validation status anytime
python scripts/dev/finalize_task.py --check-only --format json

# Run specific validation types
python scripts/dev/finalize_task.py --tests-only --dry-run
python scripts/dev/finalize_task.py --linting-only --dry-run
```

---

### 3. `scripts/dev/finalize_task.py`

**Purpose**: Complete all automatable validation and wrap-up for the current task

**What it does**:

1. **Run comprehensive validation** - Tests, coverage, linting, formatting
2. **Update task completion** - Mark task as complete with finish timestamp  
3. **Update change entry** - Add test results, coverage info to existing change entry
4. **Prepare for submission** - Ensure everything is ready for commit

**CLI Interface**:

```bash
# Run full finalization for current task
python scripts/dev/finalize_task.py

# Finalize specific task by ID
python scripts/dev/finalize_task.py --task-id 4

# Check validation status without making changes
python scripts/dev/finalize_task.py --check-only
```

**AI-Friendly Output**:

```json
{
  "success": true,
  "task_completed": {
    "id": 4,
    "title": "Fix failing tests in tests/test_example_module.py",
    "finish_time": "2025-07-30T06:04:10.115Z"
  },
  "validation_results": {
    "tests": {"status": "pass", "count": 15, "failures": 0},
    "coverage": {"percentage": 87, "threshold": 80, "status": "pass"},
    "linting": {"status": "pass", "issues": 0},
    "formatting": {"status": "pass", "files_changed": 0}
  },
  "change_entry_updated": "docs/changelog/main_0-1-0_20250730T124523Z.md",
  "ready_for_submission": true
}
```

---

### 4. `scripts/dev/submit_change.py`

**Purpose**: Handle final submission with human/AI summary input

**What it does**:

1. **Validate everything is ready** - Ensure finalize_task was run and passed
2. **Generate commit message template** - Based on task and change entry
3. **Request summary from human/AI** - Interactive or via parameter
4. **Stage files and commit** - With the provided summary
5. **Archive completed task** - Move to Archive section

**CLI Interface**:

```bash
# Interactive submission (prompts for summary)
python scripts/dev/submit_change.py

# Provide summary directly
python scripts/dev/submit_change.py --summary "Fixed authentication bugs and improved test coverage"

# Preview what would be committed
python scripts/dev/submit_change.py --dry-run
```

**AI-Friendly Output**:

```json
{
  "success": true,
  "commit_hash": "a1b2c3d4",
  "commit_message": "feat: Fix failing tests in test_example_module.py\n\nFixed authentication bugs and improved test coverage\n\nAddresses task #4",
  "files_committed": ["src/auth.py", "tests/test_auth.py", "docs/changelog/main_0-1-0_20250730T124523Z.md"],
  "task_archived": 4,
  "ready_for_pr": true
}
```

## Integration with Existing Scripts

### Reuses Current Scripts

- **`run_tests.py`** - For test running and task creation in `select_next_task`
- **`create_change_entry.py`** - For initial change entry creation in `select_next_task`

### File Flow

1. **`select_next_task`** creates: `docs/changelog/branch_version_timestamp.md`
2. **AI agent reads** the change entry file to understand the task
3. **`finalize_task`** updates the same change entry file with results
4. **`submit_change`** includes the change entry file in the commit

## Example Complete Workflow

```bash
# 1. Start work (creates change entry, selects task)
python scripts/dev/select_next_task.py --format json
# Returns: {"change_entry_file": "docs/changelog/main_0-1-0_20250730T124523Z.md", "selected_task": {...}}

# AI agent reads the change entry file to understand the task
# AI agent implements the solution (manual creative work)

# 2. Validate and wrap up (comprehensive validation)
python scripts/dev/finalize_task.py --format json
# Returns: {"validation_results": {...}, "ready_for_submission": true}

# 3. Submit with summary (final commit and archive)
python scripts/dev/submit_change.py --summary "Fixed authentication bugs" --format json
# Returns: {"commit_hash": "a1b2c3d", "task_archived": 4}
```

This approach creates a clear separation between automated setup/validation and manual creative work, with the change entry file serving as the communication mechanism between scripts and AI agents.
