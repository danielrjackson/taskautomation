#!/usr/bin/env python3
"""Debug script to understand test parsing logic."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts" / "dev"))

from run_tests import generate_report, parse_existing_tasks, parse_test_results, run

# Read the current TASKS.md
TASKS = pathlib.Path("docs/TASKS.md")
task_text = TASKS.read_text()

print("=== PARSING EXISTING TASKS ===")
existing_tasks = parse_existing_tasks(task_text)
for file_path, task_info in existing_tasks.items():
    print(f"File: {file_path}")
    print(f"  Checked: {task_info.checked}")
    print(f"  Subtasks: {task_info.subtasks}")
    print()

print("=== RUNNING PYTEST AND PARSING RESULTS ===")
rc, output = run("pytest -v")
print("Pytest output:")
print("-" * 50)
print(output)
print("-" * 50)

test_results = parse_test_results(output)
print(f"\nParsed {len(test_results)} test results:")
for result in test_results:
    print(f"  {result.file_path}::{result.test_name} = {result.status}")

from run_tests import group_results_by_file

current_results = group_results_by_file(test_results)
print("\nGrouped by file:")
for file_path, tests in current_results.items():
    print(f"  {file_path}:")
    for test_name, status in tests.items():
        print(f"    {test_name} = {status}")

print("\n=== GENERATING REPORT ===")
newly_fixed, newly_broken, still_failing = generate_report(current_results, existing_tasks)

print(f"Newly fixed ({len(newly_fixed)}):")
for test in newly_fixed:
    print(f"  - {test}")

print(f"Newly broken ({len(newly_broken)}):")
for test in newly_broken:
    print(f"  - {test}")

print(f"Still failing ({len(still_failing)}):")
for test in still_failing:
    print(f"  - {test}")
