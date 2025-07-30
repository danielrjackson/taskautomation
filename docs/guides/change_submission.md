# Change Submission

## 1. Testing[^1]

Make sure that all tests pass and that the code coverage has not decreased significantly before
submitting a change.

## 2. Update Documentation

If you have made changes to the code, ensure that the documentation is updated accordingly.

## 3. Check Linting

Run the linter to ensure that the code adheres to the project's coding standards. This helps
maintain code quality and readability.

## 4. Check Diffs

 Before finalizing your changes, check the diffs to ensure that only the changes you intended to
 make are included.

- Look for any unintended or unnecessary changes that may have been made.
- Check for code that may have been accidentally modified or removed.

### 5. Change Report Instructions

Record your contributions in the `/docs/changelog/` folder.

Use the [`/docs/templates/changelog/template.md`] to create a new change report.

1. Copy the template file to a new file in the `/docs/changelog/` directory.
2. Rename the file to follow the naming convention:
   - `<branch>_<version_slug>_<datetime_slug>.md`
   - e.g., `main_0-1-0_20250730T123500Z.md`

> [!IMPORTANT] Filenames must follow `<branch>_<version_slug>_<datetime_slug>.md` format.
> e.g.: `main_0-1-0_20250730T123500Z.md`
>
> - Branch names should be lowercase and use hyphens for spaces.
>   - e.g., `main`, `feature-branch`
> - Versioning follows sluggified semantic versioning.
>   - e.g., `0-1-0`
> - Date and time in changelog entries should be in the format `YYYYMMDDTHHMMSS`.
>   - e.g., `20250730T003500Z`

## 6. Update Tasks and Changelog

1. Update the [`/docs/TASKS.md`] file with a link to the change log entry file you just created.

2. If the change is significant, such as a new feature or a major bug fix, update the
[`/docs/CHANGELOG.md`] file with a summary of the change in the appropriate section[^2].

## 7. Committing Changes

> [!IMPORTANT] Use Meaningful Commit Messages
>
> Commit messages should be clear and concise, explaining what the change does and why it was made.
>
> - The reasoning behind the change should be in the body of the commit message.
>   - Without it, it requires much more effort to understand the change.
> - The subject line should be a brief summary of the change.
>   - It should be no more than 50 characters long.
> - The body of the commit message should explain the change in more detail.
>   - It should be wrapped at 72 characters.
> - Include a link to the issue or task that the change addresses.
>   - If one does not exist, create one in the [`/docs/TASKS.md`] file or the issues tracker.
>   - This allows others to see an overview of the changes that have been made without having to
>       read through the entire commit history.
>
> It should essentially be an abbreviated version of the change report, with the most important
> information included in the commit message.

### 8. Pull Requests

Before you submit a pull request, check that it meets these guidelines:

1. All previous steps have been completed, including testing and change report creation.
2. The pull request should be contained:
   - If it's too big consider splitting it into smaller pull requests.

## See Also

- [Changelog]
- [Lessons Learned]
- [Tasks]
- [Testing]

[//]: # (Links)

[`/docs/TASKS.md`]: ../TASKS.md
[`/docs/CHANGELOG.md`]: ../CHANGELOG.md
[Changelog]: ../CHANGELOG.md
[Lessons Learned]: ./lessons_learned.md
[Tasks]: ../TASKS.md
[Testing]: ./testing.md
[Unreleased]: ../CHANGELOG.md#unreleased

<!-- Footnotes -->

[^1]: *See the [Testing] document for detailed instructions on how to write and run tests for the project.*
[^2]: *This is usually the [Unreleased] section.*
