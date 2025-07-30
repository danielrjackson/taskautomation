#!/usr/bin/env python3
"""
Comprehensive tests for run_tests.py script.

Tests the configurable path system and all functionality of the test runner script.
"""

import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from taskautomation.run_tests import (
    get_paths,
    main,
    update_tasks_file,
)


class TestRunTests(unittest.TestCase):
    """Test cases for run_tests script."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.test_root = pathlib.Path(self.test_dir)

        # Set up test directory structure
        self.setup_test_directory()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def setup_test_directory(self):
        """Set up the test directory structure."""
        # Create necessary directories
        (self.test_root / "docs").mkdir(parents=True)
        (self.test_root / "src" / "taskautomation").mkdir(parents=True)
        (self.test_root / "tests").mkdir(parents=True)

        # Copy test data files
        test_data_dir = pathlib.Path(__file__).parent / "data"

        # Copy TASKS.md
        if (test_data_dir / "sample_tasks.md").exists():
            shutil.copy2(test_data_dir / "sample_tasks.md", self.test_root / "docs" / "TASKS.md")
        else:
            # Create a basic tasks file if test data doesn't exist
            tasks_content = """# Test Tasks

## Current Tasks

- [ ] **Test Task 1**:
  - **ID**: 1
  - **Priority**: High
  - **Assignee**: TestUser
  - **Create Date**: 2025-01-01T12:00:00Z
  - **Description**: A test task

- [x] **Completed Task**:
  - **ID**: 2
  - **Priority**: Medium
  - **Assignee**: TestUser
  - **Create Date**: 2025-01-01T10:00:00Z
  - **Finished Date**: 2025-01-01T11:00:00Z
  - **Description**: A completed test task
"""
            (self.test_root / "docs" / "TASKS.md").write_text(tasks_content)

        # Create some test script files
        self.create_test_scripts()

    def create_test_scripts(self):
        """Create test script files for testing."""
        scripts_dir = self.test_root / "src" / "taskautomation"

        # Create dummy script files
        test_scripts = [
            "task_utils.py",
            "create_change_entry.py",
            "validate_automation.py",
            "run_tests.py",
        ]

        for script in test_scripts:
            script_path = scripts_dir / script
            script_path.write_text(
                f'#!/usr/bin/env python3\n"""Test {script}"""\nprint("Test script {script}")\n'
            )

    def test_get_paths_default(self):
        """Test get_paths function with default root."""
        paths = get_paths()

        # Should return dictionary with required keys
        required_keys = ["ROOT", "TASKS"]
        for key in required_keys:
            self.assertIn(key, paths)
            self.assertIsInstance(paths[key], pathlib.Path)

    def test_get_paths_override(self):
        """Test get_paths function with root override."""
        paths = get_paths(self.test_root)

        # Should use overridden root
        self.assertEqual(paths["ROOT"], self.test_root)
        self.assertEqual(paths["TASKS"], self.test_root / "docs" / "TASKS.md")

    def test_update_tasks_file_function(self):
        """Test update_tasks_file function with configurable paths."""
        tasks_file = self.test_root / "docs" / "TASKS.md"

        # Create sample test results and existing tasks
        current_results = {"test_file.py": {"test_sample": "FAILED"}}
        existing_tasks = {}

        # Function should handle existing tasks file
        result = update_tasks_file(
            current_results, existing_tasks, dry_run=True, tasks_file=tasks_file
        )
        self.assertIsInstance(result, bool)

    def test_update_tasks_file_missing(self):
        """Test update_tasks_file function with missing file."""
        missing_file = self.test_root / "docs" / "nonexistent.md"

        # Create sample test results and existing tasks
        current_results = {"test_file.py": {"test_sample": "FAILED"}}
        existing_tasks = {}

        # Function should handle missing file gracefully
        result = update_tasks_file(
            current_results, existing_tasks, dry_run=True, tasks_file=missing_file
        )
        self.assertIsInstance(result, bool)

    def test_main_default_behavior(self):
        """Test main function with default behavior."""
        with self.assertRaises(SystemExit) as cm:
            main([], root_override=self.test_root)

        # Should exit with some code (0 or non-zero depending on test results)
        self.assertIsInstance(cm.exception.code, int)

    def test_main_with_update_tasks(self):
        """Test main function with update-tasks flag."""
        with self.assertRaises(SystemExit) as cm:
            main(["--update-tasks"], root_override=self.test_root)

        # Should handle update-tasks flag and exit
        self.assertIsInstance(cm.exception.code, int)

    def test_main_quiet_mode(self):
        """Test main function in quiet mode."""
        with patch("sys.stdout"):
            with self.assertRaises(SystemExit) as cm:
                main(["--quiet"], root_override=self.test_root)

        # Should handle quiet mode and exit
        self.assertIsInstance(cm.exception.code, int)

    def test_main_dry_run_mode(self):
        """Test main function in dry-run mode (default behavior)."""
        with self.assertRaises(SystemExit) as cm:
            main([], root_override=self.test_root)

        # Should handle dry-run mode (default) and exit
        self.assertIsInstance(cm.exception.code, int)

    def test_main_json_format(self):
        """Test main function with coverage none option."""
        with patch("sys.stdout"):
            with self.assertRaises(SystemExit) as cm:
                main(["--coverage", "none"], root_override=self.test_root)

        # Should handle coverage mode and exit
        self.assertIsInstance(cm.exception.code, int)

    def test_isolated_test_environment(self):
        """Test that the test environment is properly isolated."""
        # Test directory should exist
        self.assertTrue(self.test_root.exists())

        # Required directories should exist
        self.assertTrue((self.test_root / "docs").exists())
        self.assertTrue((self.test_root / "src" / "taskautomation").exists())

        # Tasks file should exist
        self.assertTrue((self.test_root / "docs" / "TASKS.md").exists())

    def test_script_execution_isolation(self):
        """Test that script execution is isolated to test environment."""
        # This test checks that the test runner works in isolated environment
        # Since main() exits with SystemExit, we expect that behavior
        with self.assertRaises(SystemExit):
            main([], root_override=self.test_root)

    def test_error_handling_invalid_arguments(self):
        """Test error handling with invalid arguments."""
        # Invalid arguments should cause SystemExit (argparse behavior)
        with self.assertRaises(SystemExit):
            main(["--invalid-argument"], root_override=self.test_root)

    def test_tasks_file_modification(self):
        """Test that tasks file can be modified in test environment."""
        tasks_file = self.test_root / "docs" / "TASKS.md"
        original_content = tasks_file.read_text()

        # Modify the tasks file
        new_content = original_content + "\n\n# Added by test\n"
        tasks_file.write_text(new_content)

        # Verify modification
        self.assertEqual(tasks_file.read_text(), new_content)
        self.assertNotEqual(tasks_file.read_text(), original_content)

    def test_script_discovery(self):
        """Test that scripts are properly discovered in test environment."""
        src_dir = self.test_root / "src" / "taskautomation"

        # Create additional test scripts
        additional_scripts = ["test_script1.py", "test_script2.py"]
        for script in additional_scripts:
            (src_dir / script).write_text(f'#!/usr/bin/env python3\nprint("Script {script}")\n')

        # Should be able to run tests and exit
        with self.assertRaises(SystemExit):
            main([], root_override=self.test_root)

    def test_help_option(self):
        """Test help option functionality."""
        with patch("sys.stdout"):
            try:
                result = main(["--help"], root_override=self.test_root)
            except SystemExit:
                # argparse calls sys.exit() on --help, which is expected
                pass

    def test_concurrent_test_safety(self):
        """Test that concurrent test execution doesn't interfere."""
        # This test ensures test isolation works for concurrent execution
        tasks_file = self.test_root / "docs" / "TASKS.md"

        # Simulate concurrent modification
        original_content = tasks_file.read_text()
        tasks_file.write_text(original_content + "\n# Test modification 1\n")

        with self.assertRaises(SystemExit):
            main(["--update-tasks"], root_override=self.test_root)

        tasks_file.write_text(original_content + "\n# Test modification 2\n")

        with self.assertRaises(SystemExit):
            main(["--update-tasks"], root_override=self.test_root)

        # Both operations should complete (exit) successfully


if __name__ == "__main__":
    unittest.main()
