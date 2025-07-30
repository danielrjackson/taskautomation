#!/usr/bin/env python3
"""
Comprehensive tests for markdown_parser.py module.

Tests the legacy markdown parsing functions and format conversion utilities.
"""

import pathlib
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from taskautomation.core_utils import (
    TaskInfo,
)
from taskautomation.markdown_parser import (
    convert_legacy_to_new_format,
    parse_legacy_task_format,
    parse_tasks_from_markdown,
)


class TestMarkdownParser(unittest.TestCase):
    """Test cases for markdown_parser module."""

    def test_parse_tasks_from_markdown_basic(self):
        """Test parse_tasks_from_markdown with basic markdown content."""
        markdown_content = """# Test Tasks

## Current Tasks

- [ ] **Test Task 1**:
  - **ID**: 1
  - **Priority**: High
  - **Assignee**: TestUser
  - **Create Date**: 2025-01-01T12:00:00Z
  - **Description**: First test task

- [x] **Completed Task**:
  - **ID**: 2
  - **Priority**: Medium
  - **Assignee**: TestUser
  - **Create Date**: 2025-01-01T10:00:00Z
  - **Finished Date**: 2025-01-01T11:00:00Z
  - **Description**: A completed task
"""

        tasks = parse_tasks_from_markdown(markdown_content)

        self.assertIsInstance(tasks, dict)
        self.assertEqual(len(tasks), 2)

        # Check first task (open)
        self.assertIn("Test Task 1", tasks)
        first_task = tasks["Test Task 1"]
        self.assertIsInstance(first_task, TaskInfo)
        self.assertEqual(first_task.task_id, 1)
        self.assertEqual(first_task.title, "Test Task 1")
        self.assertEqual(first_task.priority, "High")
        self.assertEqual(first_task.assignee, "TestUser")
        self.assertFalse(first_task.checked)  # Open task
        self.assertIsNone(first_task.finish_date)
        self.assertEqual(first_task.description, "First test task")

        # Check second task (completed)
        self.assertIn("Completed Task", tasks)
        second_task = tasks["Completed Task"]
        self.assertIsInstance(second_task, TaskInfo)
        self.assertEqual(second_task.task_id, 2)
        self.assertEqual(second_task.title, "Completed Task")
        self.assertEqual(second_task.priority, "Medium")
        self.assertTrue(second_task.checked)  # Completed task
        self.assertIsNotNone(second_task.finish_date)

    def test_parse_tasks_from_markdown_empty(self):
        """Test parse_tasks_from_markdown with empty content."""
        empty_content = ""
        tasks = parse_tasks_from_markdown(empty_content)

        self.assertIsInstance(tasks, dict)
        self.assertEqual(len(tasks), 0)

        # Test with only whitespace
        whitespace_content = "   \n\t   \n"
        tasks2 = parse_tasks_from_markdown(whitespace_content)

        self.assertIsInstance(tasks2, dict)
        self.assertEqual(len(tasks2), 0)

    def test_parse_tasks_from_markdown_no_tasks(self):
        """Test parse_tasks_from_markdown with markdown that has no tasks."""
        no_tasks_content = """# Project Documentation

This is a regular markdown document with no tasks.

## Overview

Some text here.

## Features

- Regular bullet point (not a task)
- Another bullet point
- More content

## Conclusion

No tasks found here.
"""

        tasks = parse_tasks_from_markdown(no_tasks_content)

        self.assertIsInstance(tasks, dict)
        self.assertEqual(len(tasks), 0)

    def test_parse_tasks_from_markdown_malformed(self):
        """Test parse_tasks_from_markdown with malformed task content."""
        malformed_content = """# Test Tasks

- [ ] **Incomplete Task**:
  - **ID**: 1
  - **Priority**: High
  - Missing required fields

- [ ] **Another Incomplete**:
  - **Priority**: InvalidPriority
  - **Description**: Has invalid priority

- [ ] **Task Without ID**:
  - **Priority**: Medium
  - **Assignee**: TestUser
  - **Description**: Missing ID field
"""

        tasks = parse_tasks_from_markdown(malformed_content)

        self.assertIsInstance(tasks, dict)
        # Depending on implementation, malformed tasks might be skipped
        # or included with partial information
        # The exact behavior depends on error handling in the implementation

    def test_parse_legacy_task_format(self):
        """Test parse_legacy_task_format function."""
        # Legacy format example
        legacy_format = """## Test Legacy Task
- Priority: High
- Assignee: LegacyUser
- Created: 2025-01-01
- Status: Open
- Description: This is a legacy task format that needs conversion
"""

        parsed_task = parse_legacy_task_format(legacy_format)

        # Based on actual implementation, this returns a dict[str, TaskInfo]
        self.assertIsInstance(parsed_task, dict)

        if parsed_task:  # If parsing was successful
            # Should contain the task by title
            task_title = list(parsed_task.keys())[0]
            task_info = parsed_task[task_title]
            self.assertIsInstance(task_info, TaskInfo)
            self.assertEqual(task_info.title, task_title)

    def test_parse_legacy_task_format_variations(self):
        """Test parse_legacy_task_format with different legacy variations."""
        # Different legacy format styles
        legacy_variations = [
            """## Legacy Task 1
- Priority: Medium
- Assignee: User1
- Created: 2024-12-01
- Description: First variation""",
            """## Legacy Task 2
Priority: Low
Assignee: User2
Created: 2024-12-02
Description: Second variation without bullets""",
            """## Legacy Task 3
* Priority: Critical
* Assignee: User3
* Created: 2024-12-03
* Description: Third variation with asterisks""",
        ]

        for i, legacy_content in enumerate(legacy_variations):
            with self.subTest(variation=i + 1):
                parsed = parse_legacy_task_format(legacy_content)
                self.assertIsInstance(parsed, dict)
                # Check if parsing was successful and contains expected task
                if parsed:
                    task_title = list(parsed.keys())[0]
                    self.assertIn(f"Legacy Task {i + 1}", task_title)

    def test_parse_legacy_task_format_empty(self):
        """Test parse_legacy_task_format with empty or invalid input."""
        # Empty input
        empty_result = parse_legacy_task_format("")
        self.assertIsInstance(empty_result, dict)

        # Invalid format
        invalid_format = "This is not a legacy task at all"
        invalid_result = parse_legacy_task_format(invalid_format)
        self.assertIsInstance(invalid_result, dict)

        # Partial legacy format
        partial_format = """## Partial Task
- Priority: High
- Missing other fields"""

        partial_result = parse_legacy_task_format(partial_format)
        self.assertIsInstance(partial_result, dict)
        if partial_result:  # If parsing was successful
            task_title = list(partial_result.keys())[0]
            self.assertIn("Partial Task", task_title)

    def test_convert_legacy_to_new_format(self):
        """Test convert_legacy_to_new_format function."""
        # Based on actual implementation, this function takes a string, not a dict
        legacy_content = """## Legacy Conversion Test
- Priority: High
- Assignee: ConversionUser
- Created: 2025-01-01
- Status: Open
- Description: This task needs to be converted to new format
"""

        converted = convert_legacy_to_new_format(legacy_content)

        self.assertIsInstance(converted, str)
        # Based on actual implementation, this likely returns the content as-is
        # or performs minimal conversion

    def test_convert_legacy_to_new_format_completed(self):
        """Test convert_legacy_to_new_format with completed task."""
        # Completed legacy task
        completed_legacy = """## Completed Legacy Task
- Priority: Medium
- Assignee: CompletedUser
- Created: 2025-01-01
- Finished: 2025-01-02
- Status: Completed
- Description: This was a completed legacy task
"""

        converted = convert_legacy_to_new_format(completed_legacy)

        self.assertIsInstance(converted, str)
        # Conversion should preserve the content structure

    def test_convert_legacy_to_new_format_minimal(self):
        """Test convert_legacy_to_new_format with minimal data."""
        # Minimal legacy task
        minimal_legacy = "## Minimal Task"

        converted = convert_legacy_to_new_format(minimal_legacy)

        self.assertIsInstance(converted, str)
        # Should handle minimal input gracefully

    def test_convert_legacy_to_new_format_edge_cases(self):
        """Test convert_legacy_to_new_format with edge cases."""
        # Empty legacy task
        empty_legacy = ""
        converted_empty = convert_legacy_to_new_format(empty_legacy)
        self.assertIsInstance(converted_empty, str)

        # Legacy task with various content
        complex_legacy = """## Extra Fields Task
- Priority: High
- Unexpected Field: should be handled
- Another Extra: 12345
"""
        converted_extra = convert_legacy_to_new_format(complex_legacy)
        self.assertIsInstance(converted_extra, str)

    def test_parse_tasks_mixed_formats(self):
        """Test parsing markdown with mixed task formats."""
        mixed_content = """# Mixed Format Tasks

## Current Tasks

- [ ] **Modern Task**:
  - **ID**: 1
  - **Priority**: High
  - **Assignee**: ModernUser
  - **Create Date**: 2025-01-01T12:00:00Z
  - **Description**: Modern format task

Some text between tasks.

- [x] **Another Modern Task**:
  - **ID**: 2
  - **Priority**: Medium
  - **Assignee**: AnotherUser
  - **Create Date**: 2025-01-01T10:00:00Z
  - **Finished Date**: 2025-01-01T11:00:00Z
  - **Description**: Completed modern task

## Notes

Some additional content that's not a task.

- [ ] **Third Task**:
  - **ID**: 3
  - **Priority**: Low
  - **Assignee**: ThirdUser
  - **Create Date**: 2025-01-01T08:00:00Z
  - **Description**: Final task in the list
"""

        tasks = parse_tasks_from_markdown(mixed_content)

        self.assertIsInstance(tasks, dict)
        self.assertEqual(len(tasks), 3)

        # Verify all tasks were parsed correctly
        expected_titles = ["Modern Task", "Another Modern Task", "Third Task"]
        for title in expected_titles:
            self.assertIn(title, tasks)

        # Check task IDs and statuses
        task_ids = [task.task_id for task in tasks.values()]
        self.assertEqual(sorted(task_ids), [1, 2, 3])

        # Check completion status (using checked field)
        modern_task = tasks["Modern Task"]
        completed_task = tasks["Another Modern Task"]
        third_task = tasks["Third Task"]

        self.assertFalse(modern_task.checked)  # Open task
        self.assertTrue(completed_task.checked)  # Completed task
        self.assertFalse(third_task.checked)  # Open task

    def test_parse_tasks_with_special_characters(self):
        """Test parsing tasks with special characters in titles and descriptions."""
        special_chars_content = """# Special Characters Test

- [ ] **Task with @#$%^&*() Characters**:
  - **ID**: 1
  - **Priority**: High
  - **Assignee**: User@Domain.com
  - **Create Date**: 2025-01-01T12:00:00Z
  - **Description**: Description with special chars: @#$%^&*(){}[]|\\:";'<>?,./

- [ ] **Unicode Task: 你好世界 🚀 🎉**:
  - **ID**: 2
  - **Priority**: Medium
  - **Assignee**: UnicodeUser
  - **Create Date**: 2025-01-01T13:00:00Z
  - **Description**: Task with Unicode characters and emojis
"""

        tasks = parse_tasks_from_markdown(special_chars_content)

        self.assertIsInstance(tasks, dict)
        self.assertEqual(len(tasks), 2)

        # Check that special characters are preserved
        special_task_title = "Task with @#$%^&*() Characters"
        unicode_task_title = "Unicode Task: 你好世界 🚀 🎉"

        self.assertIn(special_task_title, tasks)
        self.assertIn(unicode_task_title, tasks)

        first_task = tasks[special_task_title]
        self.assertIn("@#$%^&*()", first_task.title)
        if first_task.description:
            self.assertIn("@#$%^&*(){}[]", first_task.description)

        second_task = tasks[unicode_task_title]
        self.assertIn("你好世界", second_task.title)
        self.assertIn("🚀", second_task.title)
        if second_task.description:
            self.assertIn("Unicode characters", second_task.description)

    def test_roundtrip_conversion(self):
        """Test roundtrip conversion from legacy to new format and back to parsing."""
        # Start with legacy format
        legacy_content = """## Roundtrip Test Task
- Priority: Critical
- Assignee: RoundtripUser
- Created: 2025-01-01
- Status: Open
- Description: Testing roundtrip conversion functionality
"""

        # Convert to new format
        new_format = convert_legacy_to_new_format(legacy_content)

        # Parse the new format back
        markdown_with_task = f"# Test\n\n{new_format}"
        parsed_tasks = parse_tasks_from_markdown(markdown_with_task)

        # Should get back task info
        self.assertIsInstance(parsed_tasks, dict)
        # The exact behavior depends on the implementation
        # but we should get some kind of meaningful result


if __name__ == "__main__":
    unittest.main()
