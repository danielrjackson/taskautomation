# Task Workflow Automation Plan (Revised - Modular Approach)

This document outlines the plan for automating the "pick a task, do a task, test the change, finalize the change, submit" workflow process with a focus on **modular, single-purpose scripts** that can be used independently for "check your work" validation.

## Current State Analysis

### Existing Scripts

- [`scripts/dev/create_change_entry.py`](../scripts/dev/create_change_entry.py) - Creates changelog entries
- [`scripts/dev/run_tests.py`](../scripts/dev/run_tests.py) - Runs tests and manages test-related tasks
- [`scripts/dev/debug_test_parser.py`](../scripts/dev/debug_test_parser.py) - Test output parsing utilities

### Current Workflow (Manual Steps)

1. **Pick a task** - Manual selection from TASKS.md
2. **Do the task** - Manual implementation (requires human/AI intelligence)
3. **Test the change** - Partially automated via run_tests.py
4. **Finalize the change** - Manual task completion, change entry creation
5. **Submit the change** - Manual git operations and PR creation

## Core Design Principle: Modular "Check Your Work" Scripts

Following the successful pattern of [`run_tests.py`](../scripts/dev/run_tests.py), each script:

- **Does one thing well** - Single responsibility
- **Can be used independently** - Standalone validation
- **Provides "check your work" modes** - Preview/dry-run options
- **Can be composed together** - Scripts call other scripts when needed
- **Fails fast with clear feedback** - Easy debugging

## Proposed Modular Automation Scripts

### 1. Task Creation: `scripts/dev/create_task.py`

**Single Purpose**: Create new tasks in TASKS.md

**CLI Interface**:

```bash
# Minimal required args (title, description)
python scripts/dev/create_task.py "Fix user authentication bug" \
  "Login form not validating email addresses properly"

# With optional parameters  
python scripts/dev/create_task.py "Fix user authentication bug" \
  "Login form not validating email addresses properly" \
  --priority Critical --estimated-time "2 hours" --assignee Roo
```

**"Check Your Work" Features**:

```bash
# Preview task without creating it (dry-run)
python scripts/dev/create_task.py --dry-run "New task" "Task description"

# Check if task would be duplicate
python scripts/dev/create_task.py --check-duplicate "Fix user authentication bug"

# Show what the next task ID would be
python scripts/dev/create_task.py --next-id
```

### 2. Task Status Management: `scripts/dev/update_task.py`

**Single Purpose**: Update task status, timestamps, and metadata

**CLI Interface**:

```bash
# Mark task as started (adds start timestamp)
python scripts/dev/update_task.py --task-id 4 --start

# Mark task as completed (adds finish timestamp)
python scripts/dev/update_task.py --task-id 4 --complete

# Update specific fields
python scripts/dev/update_task.py --task-id 4 --assignee "Alice" --estimated-time "3 hours"
```

**"Check Your Work" Features**:

```bash
# Show current task status without changes
python scripts/dev/update_task.py --task-id 4 --status

# Preview changes without applying (dry-run)
python scripts/dev/update_task.py --task-id 4 --complete --dry-run

# List all tasks with their current status
python scripts/dev/update_task.py --list-all
```

### 3. Task Archival: `scripts/dev/archive_tasks.py`

**Single Purpose**: Move completed tasks to archive section

**CLI Interface**:

```bash
# Archive specific completed tasks
python scripts/dev/archive_tasks.py --task-ids 4,5,6

# Archive all completed tasks
python scripts/dev/archive_tasks.py --all-completed

# Interactive selection of tasks to archive
python scripts/dev/archive_tasks.py --interactive
```

**"Check Your Work" Features**:

```bash
# List tasks ready for archival (completed but not archived)
python scripts/dev/archive_tasks.py --list-completed

# Preview archival without actually moving tasks (dry-run)
python scripts/dev/archive_tasks.py --all-completed --dry-run

# Show archive statistics
python scripts/dev/archive_tasks.py --stats
```

### 4. Pre-submission Validation: `scripts/dev/validate_changes.py`  

**Single Purpose**: Run all pre-submission checks (extends run_tests.py pattern)

**CLI Interface**:

```bash
# Run all validation checks
python scripts/dev/validate_changes.py

# Run specific check types
python scripts/dev/validate_changes.py --tests-only
python scripts/dev/validate_changes.py --linting-only
python scripts/dev/validate_changes.py --coverage-only

# Fast validation (skip slow checks)
python scripts/dev/validate_changes.py --fast
```

**"Check Your Work" Features**:

```bash
# List what validation checks would run
python scripts/dev/validate_changes.py --list-checks

# Validate specific files only
python scripts/dev/validate_changes.py --files src/auth.py tests/test_auth.py

# Check validation status without running (what needs attention)
python scripts/dev/validate_changes.py --check-status
```

### 5. Change Entry Generation: `scripts/dev/generate_change_entry.py`

**Single Purpose**: Generate change entries for completed tasks

**CLI Interface**:

```bash
# Generate entry for specific task (calls existing create_change_entry.py)
python scripts/dev/generate_change_entry.py --task-id 4

# Generate entries for multiple completed tasks  
python scripts/dev/generate_change_entry.py --task-ids 4,5,6

# Generate entry with custom details
python scripts/dev/generate_change_entry.py --task-id 4 --custom-title "Major Auth Fix"
```

**"Check Your Work" Features**:

```bash
# Preview change entry without creating file
python scripts/dev/generate_change_entry.py --task-id 4 --preview

# List tasks ready for change entries (completed but no entry exists)
python scripts/dev/generate_change_entry.py --list-ready

# Validate existing change entry format
python scripts/dev/generate_change_entry.py --validate-existing
```

### 6. Git Integration: `scripts/dev/prepare_commit.py`

**Single Purpose**: Prepare git operations for task completion

**CLI Interface**:

```bash
# Generate commit message for task
python scripts/dev/prepare_commit.py --task-id 4

# Stage relevant files and generate message
python scripts/dev/prepare_commit.py --task-id 4 --stage-files

# Interactive file selection for staging
python scripts/dev/prepare_commit.py --task-id 4 --interactive
```

**"Check Your Work" Features**:

```bash
# Preview commit message without staging anything
python scripts/dev/prepare_commit.py --task-id 4 --preview

# Check git status and what's ready to commit
python scripts/dev/prepare_commit.py --check-status

# Validate commit message format
python scripts/dev/prepare_commit.py --validate-message "commit message here"
```

## Script Composition Pattern

Scripts can call each other but remain independently useful:

### Example: Task Completion Workflow

```bash
# Step 1: Validate your work is ready
python scripts/dev/validate_changes.py

# Step 2: Mark task as complete  
python scripts/dev/update_task.py --task-id 4 --complete

# Step 3: Generate change entry
python scripts/dev/generate_change_entry.py --task-id 4

# Step 4: Prepare commit
python scripts/dev/prepare_commit.py --task-id 4 --stage-files

# Each step can be run independently for validation
```

### Example: "Check Your Work" Validation Chain

```bash
# Quick validation checklist
python scripts/dev/validate_changes.py --check-status     # Are tests/linting ready?
python scripts/dev/update_task.py --task-id 4 --status   # Is task properly updated?
python scripts/dev/generate_change_entry.py --list-ready # Do I need change entries?
python scripts/dev/prepare_commit.py --check-status      # What's ready to commit?
```

## File Structure

```
scripts/dev/
├── create_task.py              # NEW - Task creation
├── update_task.py              # NEW - Task status management  
├── archive_tasks.py            # NEW - Task archival
├── validate_changes.py         # NEW - Pre-submission validation
├── generate_change_entry.py    # NEW - Change entry generation
├── prepare_commit.py           # NEW - Git preparation
├── create_change_entry.py      # EXISTING - Changelog creation (called by generate_change_entry.py)
├── run_tests.py                # EXISTING - Test management (called by validate_changes.py)
├── debug_test_parser.py        # EXISTING - Test utilities
└── task_utils.py               # NEW - Shared task management utilities
```

## Implementation Priority

### Phase 1: Core Task Management (Week 1)

1. **`task_utils.py`** - Shared utilities for parsing/updating TASKS.md
2. **`create_task.py`** - New task creation with validation
3. **`update_task.py`** - Task status management
4. **`archive_tasks.py`** - Task archival system

**Deliverable**: Complete task lifecycle management with "check your work" features

### Phase 2: Validation Enhancement (Week 2)  

1. **`validate_changes.py`** - Enhanced pre-submission validation
2. **Integration with existing `run_tests.py`** - Compose validation checks
3. **Linting/coverage integration** - Add additional validation types

**Deliverable**: Comprehensive validation system you can run anytime

### Phase 3: Change Management (Week 3)

1. **`generate_change_entry.py`** - Change entry automation  
2. **`prepare_commit.py`** - Git integration and commit preparation
3. **Integration testing** - All scripts work together

**Deliverable**: Full change management automation

### Phase 4: Polish and Documentation (Week 4)

1. **Documentation** - Usage examples, "check your work" guides
2. **Error handling** - Robust error scenarios and recovery
3. **Testing** - Test the automation scripts themselves

**Deliverable**: Production-ready automation suite

## Key Benefits of This Modular Approach

### Individual Script Usage

- **Before starting work**: `create_task.py --dry-run` to plan task
- **During work**: `validate_changes.py --check-status` to see what needs attention  
- **Before committing**: `prepare_commit.py --preview` to check commit message
- **After completion**: `archive_tasks.py --list-completed` to see what can be archived

### Composed Workflow Usage

- Scripts can be chained together for full automation
- Each step can be validated independently  
- Easy to debug where things go wrong
- Can skip steps that aren't needed for a particular change

### "Check Your Work" Philosophy

Every script answers the question: "What would happen if I ran this?" before you actually run it, following the successful pattern established by your [`run_tests.py`](../scripts/dev/run_tests.py) script.

This gives you the reliability and predictability of automation while maintaining the flexibility to validate and intervene at any step.
