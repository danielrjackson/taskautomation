# AI Agent Considerations for Task Automation

## Overview

The task automation scripts should be designed to make AI agents' lives easier by providing structured, predictable interfaces that can be easily parsed and automated.

## AI-Friendly Design Principles

### 1. Structured Output Formats

All scripts should support machine-readable output:

```bash
# Human-readable output (default)
python scripts/dev/finish_tasks.py --task-ids 4,5

# JSON output for AI agents
python scripts/dev/finish_tasks.py --task-ids 4,5 --format json
```

**Example JSON Output:**

```json
{
  "success": true,
  "tasks_processed": [
    {
      "id": 4,
      "title": "Fix failing tests in tests/test_example_module.py",
      "action": "finished",
      "finish_time": "2025-07-30T05:44:17.442Z",
      "archived": true
    },
    {
      "id": 5,
      "title": "Create Tasks",
      "action": "finished", 
      "finish_time": "2025-07-30T05:44:17.442Z",
      "archived": true
    }
  ],
  "change_entry_file": "docs/changelog/main_0-1-0_20250730T124523Z.md",
  "commit_message": "feat: Complete authentication and task management work\n\nAddresses tasks #4, #5:\n- Fixed failing tests in test_example_module.py\n- Created initial task structure and documentation"
}
```

### 2. Predictable Exit Codes

Standardized exit codes for automation:

```python
# Exit codes for all scripts
EXIT_SUCCESS = 0           # Operation completed successfully
EXIT_NO_WORK = 1          # Nothing to do (no tasks found, etc.)
EXIT_VALIDATION_ERROR = 2  # Validation failed (task not found, invalid state)
EXIT_SYSTEM_ERROR = 3     # System error (file not found, permissions, etc.)
EXIT_USER_ABORT = 4       # User aborted operation (in interactive mode)
```

### 3. Machine-Readable Status Queries

Quick status checks without side effects:

```bash
# Check what tasks are ready to finish (no changes made)
python scripts/dev/finish_tasks.py --status --format json
# Returns: {"ready_tasks": [4, 5], "count": 2, "needs_attention": []}

# Check validation status
python scripts/dev/validate_changes.py --status --format json  
# Returns: {"tests": "pass", "linting": "fail", "coverage": 85, "ready": false}

# Check task information
python scripts/dev/update_task.py --task-id 4 --status --format json
# Returns: {"id": 4, "title": "...", "status": "completed", "needs_finish": true}
```

### 4. Batch Operations with Progress

AI agents can process multiple tasks efficiently:

```bash
# Process multiple tasks with progress info
python scripts/dev/finish_tasks.py --task-ids 4,5,6,7 --format json --progress
```

**Streaming JSON Output:**

```json
{"type": "progress", "task_id": 4, "action": "starting", "total": 4, "current": 1}
{"type": "progress", "task_id": 4, "action": "finished", "total": 4, "current": 1}
{"type": "progress", "task_id": 5, "action": "starting", "total": 4, "current": 2}
{"type": "progress", "task_id": 5, "action": "finished", "total": 4, "current": 2}
{"type": "result", "success": true, "tasks_processed": [...]}
```

### 5. Standardized CLI Interface Pattern

All scripts follow the same interface pattern:

```bash
# Standard pattern for all scripts
python scripts/dev/{script_name}.py [TARGETS] [OPTIONS]

# Where:
# TARGETS: --task-id 4, --task-ids 4,5,6, --all, etc.
# OPTIONS: --dry-run, --format json, --quiet, --status, --interactive
```

### 6. Error Handling for AI Agents

Structured error information:

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID 4 not found",
    "details": {
      "requested_id": 4,
      "available_ids": [1, 2, 3],
      "suggestion": "Use --list to see available tasks"
    }
  }
}
```

### 7. AI Agent Workflow Integration

Scripts designed for easy chaining by AI agents:

```python
# AI agent can easily chain operations
def complete_task_workflow(task_ids: list[int]):
    # Step 1: Validate
    result = run_script("validate_changes.py", ["--format", "json"])
    if not result["ready"]:
        return {"error": "Validation failed", "details": result}
    
    # Step 2: Finish tasks
    result = run_script("finish_tasks.py", ["--task-ids", ",".join(map(str, task_ids)), "--format", "json"])
    if not result["success"]:
        return result
    
    # Step 3: Generate change entry
    result = run_script("generate_change_entry.py", ["--task-ids", ",".join(map(str, task_ids)), "--format", "json"])
    
    return result
```

### 8. Configuration via Environment Variables

AI agents can configure behavior via environment:

```bash
# AI agent sets preferences
export TASK_AUTOMATION_FORMAT=json
export TASK_AUTOMATION_QUIET=true
export TASK_AUTOMATION_DRY_RUN=false

# Scripts respect these settings
python scripts/dev/finish_tasks.py --task-ids 4,5
# Automatically uses JSON format and quiet mode
```

### 9. Self-Documentation for AI Agents

Scripts provide machine-readable help:

```bash
python scripts/dev/finish_tasks.py --help --format json
```

**Returns schema information:**

```json
{
  "script": "finish_tasks.py",
  "purpose": "Wrap up completed tasks and prepare for change entries",
  "required_args": [],
  "optional_args": [
    {"name": "--task-ids", "type": "comma_separated_ints", "description": "Specific task IDs to finish"},
    {"name": "--dry-run", "type": "flag", "description": "Preview changes without applying"}
  ],
  "exit_codes": {
    "0": "Success",
    "1": "No work to do", 
    "2": "Validation error",
    "3": "System error"
  },
  "output_formats": ["human", "json"],
  "examples": [
    {"command": "finish_tasks.py --task-ids 4,5", "description": "Finish specific tasks"},
    {"command": "finish_tasks.py --dry-run", "description": "Preview what would be finished"}
  ]
}
```

## Implementation Guidelines

### Script Template Structure

```python
#!/usr/bin/env python3
"""
AI-friendly task automation script template
"""

import json
import sys
from enum import IntEnum
from typing import Dict, Any, List

class ExitCode(IntEnum):
    SUCCESS = 0
    NO_WORK = 1
    VALIDATION_ERROR = 2
    SYSTEM_ERROR = 3
    USER_ABORT = 4

def output_result(data: Dict[str, Any], format_type: str = "human") -> None:
    """Output results in human or JSON format"""
    if format_type == "json":
        print(json.dumps(data, indent=2))
    else:
        # Human-readable output
        print_human_readable(data)

def main():
    # Parse args, detect --format json
    # Perform operations
    # Always return structured data that can be output in either format
    result = {"success": True, "data": {...}}
    output_result(result, args.format)
    sys.exit(ExitCode.SUCCESS)
```

This AI-friendly design ensures that both human users and AI agents can efficiently use the automation scripts, with AI agents getting the structured, predictable interfaces they need for reliable automation.
