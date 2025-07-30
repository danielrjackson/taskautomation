# Testing

> [!IMPORTANT] Create Tests
>
> If you are adding new functionality, please create tests for it.
> If you are fixing a bug, please create a test that reproduces the bug.
> This will help ensure that the bug is fixed and that it doesn't come back in the future.
> See the [Testing] section for more information on how to write tests.

> [!IMPORTANT] Write Tests First
>
> Write tests before you write the code.
> This helps ensure that the code is correct and that it works as intended.

> [!IMPORTANT] Write Tests that Cover important Code Paths and Edge Cases
>
> Make sure to write tests that are meaningful and comprehensive, not just little stubs.
>
> Think carefully about edge cases and how the code will be used. Try to poke at the code where it
> is most likely to break.

> [!CAUTION] Add Tests for New Features and Bug Fixes
>
> If you are adding new functionality, please create tests for it.
> If you are fixing a bug, please create a test that reproduces the bug.
>
> - This will help ensure that the bug is fixed and that it doesn't come back in the future.

## Running Tests

To run the tests, use the following command:

```bash
pytest --cov=taskautomation --cov-report=html
```

## Coverage Report

> [!TIP] Use the Coverage Report
>
> The coverage report will be generated in the `htmlcov` directory.
> You can open the `index.html` file in a web browser to view the coverage report.
> This report will show you which lines of code are covered by tests and which are not.

Alternatively, you can run the tests with the following command to see the coverage report in the
terminal (Especially useful for AI agents):

```bash
pytest --cov=taskautomation --cov-report=term-missing
```

Make sure that the test coverage does not decrease significantly. You can check the old coverage
percentage by looking at the previous changelog entry (the one with the most recent date).

## See Also

- [Authors]
- [Changelog]
- [Contributors] [^1]
- [Tasks]

[//]: # (Links)

[Testing]: #testing
[Authors]: ../AUTHORS.md
[Changelog]: ../CHANGELOG.md
[Contributors]: ../CONTRIBUTORS.md
[Tasks]: ../TASKS.md
[AI Assistants]: ../guides/ai_assistants.md

<!-- Footnotes -->

[^1]: *See [AI Assistants] for a list of AI assistants that contributed to this project.*
