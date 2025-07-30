#!/usr/bin/env python3
"""Tests for create_change_entry.py script."""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.taskautomation.create_change_entry import (
    first_task,
    get_paths,
    main,
    version,
)


class TestCreateChangeEntry(unittest.TestCase):
    """Test cases for create_change_entry.py functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.test_root = Path(self.test_dir)

        # Create necessary directory structure
        docs_dir = self.test_root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        templates_dir = docs_dir / "templates" / "changelog"
        templates_dir.mkdir(parents=True, exist_ok=True)

        changelog_dir = docs_dir / "changelog"
        changelog_dir.mkdir(parents=True, exist_ok=True)

        # Copy test data files
        test_data_dir = Path(__file__).parent / "data"

        # Copy template
        template_src = test_data_dir / "template.md"
        template_dst = templates_dir / "template.md"
        if template_src.exists():
            shutil.copy2(template_src, template_dst)

        # Copy sample tasks
        tasks_src = test_data_dir / "sample_tasks.md"
        tasks_dst = docs_dir / "TASKS.md"
        if tasks_src.exists():
            shutil.copy2(tasks_src, tasks_dst)

        # Copy pyproject.toml
        pyproject_src = test_data_dir / "pyproject.toml"
        pyproject_dst = self.test_root / "pyproject.toml"
        if pyproject_src.exists():
            shutil.copy2(pyproject_src, pyproject_dst)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_paths_default(self):
        """Test get_paths function with default parameters."""
        paths = get_paths()

        # Should return default paths (dict with all required keys)
        required_keys = ["ROOT", "TEMPLATE", "CHANGELOG_DIR", "TASKS_MD", "PYPROJECT"]
        for key in required_keys:
            self.assertIn(key, paths)
            self.assertIsInstance(paths[key], Path)

    def test_get_paths_override(self):
        """Test get_paths function with root override."""
        paths = get_paths(self.test_root)

        # Should use overridden root
        self.assertEqual(paths["ROOT"], self.test_root)
        self.assertEqual(
            paths["TEMPLATE"], self.test_root / "docs" / "templates" / "changelog" / "template.md"
        )

    def test_isolated_test_environment(self):
        """Test that test environment is properly isolated."""
        paths = get_paths(self.test_root)

        # Verify test files exist
        self.assertTrue(paths["TEMPLATE"].exists(), f"Template not found: {paths['TEMPLATE']}")
        self.assertTrue(paths["TASKS_MD"].exists(), f"Tasks file not found: {paths['TASKS_MD']}")
        self.assertTrue(paths["PYPROJECT"].exists(), f"Pyproject not found: {paths['PYPROJECT']}")

        # Verify changelog directory exists
        self.assertTrue(paths["CHANGELOG_DIR"].exists())

    def test_version_function(self):
        """Test version function."""
        result = version(root_override=self.test_root)
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Version:", result.message)

    def test_first_task_function(self):
        """Test first_task function."""
        result = first_task(root_override=self.test_root)
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        # Should either find a task or report no unchecked tasks
        self.assertTrue(
            "First task:" in result.message or "No unchecked tasks found" in result.message
        )

    def test_main_no_arguments(self):
        """Test main function with no arguments (uses defaults)."""
        # Skip coverage to prevent recursive pytest execution
        result = main(["--skip-coverage"], root_override=self.test_root)
        # main() function returns None on success and prints the output file path
        self.assertIsNone(result)

        # Verify changelog file was created
        changelog_dir = self.test_root / "docs" / "changelog"
        changelog_files = list(changelog_dir.glob("*.md"))
        self.assertGreater(len(changelog_files), 0, "No changelog file was created")

    def test_custom_arguments(self):
        """Test main function with custom arguments."""
        result = main(
            [
                "--skip-coverage",
                "--change-title",
                "Test Change",
                "--author-name",
                "Test Author",
                "--change-type",
                "feature",
            ],
            root_override=self.test_root,
        )
        # Should succeed and return None
        self.assertIsNone(result)

        # Verify changelog file was created
        changelog_dir = self.test_root / "docs" / "changelog"
        changelog_files = list(changelog_dir.glob("*.md"))
        self.assertGreater(len(changelog_files), 0)

    def test_coverage_percentage_argument(self):
        """Test main function with coverage percentage."""
        result = main(["--coverage-percentage", "85"], root_override=self.test_root)
        # Should succeed and return None
        self.assertIsNone(result)

        # Verify changelog file was created with coverage info
        changelog_dir = self.test_root / "docs" / "changelog"
        changelog_files = list(changelog_dir.glob("*.md"))
        self.assertGreater(len(changelog_files), 0)

        # Check that coverage percentage appears in the file
        changelog_content = changelog_files[0].read_text()
        self.assertIn("85%", changelog_content)

    def test_error_handling_missing_template(self):
        """Test error handling when template file is missing."""
        # Remove template file
        template_path = self.test_root / "docs" / "templates" / "changelog" / "template.md"
        if template_path.exists():
            template_path.unlink()

        # Should call sys.exit(1) when template is missing
        with self.assertRaises(SystemExit) as cm:
            main(["--skip-coverage"], root_override=self.test_root)
        self.assertEqual(cm.exception.code, 1)

    def test_error_handling_missing_tasks_file(self):
        """Test error handling when TASKS.md file is missing."""
        # Remove tasks file
        tasks_path = self.test_root / "docs" / "TASKS.md"
        if tasks_path.exists():
            tasks_path.unlink()

        # Should handle missing tasks file gracefully (creates entry without task description)
        result = main(["--skip-coverage"], root_override=self.test_root)
        self.assertIsNone(result)  # Should still succeed

        # Verify changelog file was created
        changelog_dir = self.test_root / "docs" / "changelog"
        changelog_files = list(changelog_dir.glob("*.md"))
        self.assertGreater(len(changelog_files), 0)

    def test_changelog_creation(self):
        """Test that changelog files are created with proper naming."""
        result = main(
            ["--skip-coverage", "--change-title", "Test Entry"], root_override=self.test_root
        )
        self.assertIsNone(result)

        # Check that a changelog file was created
        changelog_dir = self.test_root / "docs" / "changelog"
        changelog_files = list(changelog_dir.glob("*.md"))
        self.assertEqual(len(changelog_files), 1)

        # Verify file naming pattern (branch_version_timestamp.md)
        changelog_file = changelog_files[0]
        self.assertTrue(changelog_file.name.endswith(".md"))
        self.assertIn("_", changelog_file.name)  # Should contain separators

        # Verify content contains expected fields
        content = changelog_file.read_text()
        self.assertIn("Test Entry", content)
        self.assertIn("Change Information", content)


if __name__ == "__main__":
    unittest.main()
