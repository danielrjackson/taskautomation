# {change_title}

> [!IMPORTANT] Template Instructions
>
> - This is a template for documenting changes in the project.
>
> **Steps**
>
> 1. Copy this template to a new file in the [`/docs/changelog/`](../../changelog) directory.
> 2. Rename the file to follow the naming convention:
>    - Use the file name format `{branch_name}_{version_slug}_YYYYMMDDTHHmmssZ.md` for the new
>      file.
>      - **Branch Name**: The name of the branch where the change was made. (e.g. `main`)
>      - **Version Slug**: The slugified version of the version, suitable for use in file names.
>        - This should be in the format `x-x-x`, where `x` is a number. (e.g. `0-1-0`)
>      - **Date and Time**: The UTC date and time of the change in the format `YYYYMMDDTHHmmssZ`.
>        - Make sure to check the current date and time before renaming the file; you can easily
>          get this wrong if you are not careful.
>        - e.g. `20250730T003500Z`
>      - e.g. `main_0-1-0_20250730T003500Z.md`
> 3. Replace the placeholders in curly braces `{ }` with the appropriate values.
>    - See the Template Fields callout below for list of fields to fill in.
> 4. Fill in the sections with the relevant information about the change.
> 5. Delete all template callout blocks in the file after filling in the template.
>    - They are just for guidance.
>    - Callouts are denoted by `>` sections with `[!IMPORTANT]`, `[!NOTE]`, or `[!TIP]` tags.

> [!NOTE] Change Log Entry Template
>
> - The links in the callout sections are kept within the callouts so that when you delete them,
>   dangling links are not left behind. They do not constitute the preferred link style for the
>   rest of the document.
> - For links, just use the inline `[Link Text]` format, and then add the full link at the bottom
>   of the file under the `[//]: # (Links)` section.
> - Avoid being overly repetitive. The sections are different for a reason.
>   - For example the [Description](#description) section should be a brief summary of ***what***
>     the change was, while the [Rationale](#rationale) section should explain ***why*** the change
>     was made.
> - If a section is not applicable, leave the heading and just put "None." in the section.
> - Don't forget to update the [`/docs/TASKS.md`](../../TASKS.md) file with a link to this change
>   log entry.
>   - This should include a link to the change log entry file.
> - Don't forget to update the [`/docs/CHANGELOG.md`](../../CHANGELOG.md) file with a link to this
>   change log entry if it is a significant change.

> [!IMPORTANT] Template Fields
>
> - **`change_title`**: A concise title for the change.
> - **`author_name`**: Your name or the name of the person making the change.
>   - You should be listed in the [`AUTHORS.md`](../../AUTHORS.md) or
>     [`CONTRIBUTORS.md`](../../guides/ai_assistants.md) file.
>     - If you are not listed, add yourself to the appropriate file.
>   - If you have a contact URL:
>     - Make it a link by surrounding it with square brackets, like `[Your Name]`.
>     - e.g. `[Daniel Jackson]`.
>   - Otherwise, just use your name without brackets.
>     - If you are an [AI agent](../../guides/ai_assistants.md#ai-assistants), just use the name of
>       the AI agent, with no links.
>     - e.g. `o3`
> - **`author_contact_url`**: A link to the author's contact information, such as an email address.
>   - Omit this if you do not have a contact URL. *(Especially if you are an AI agent.)*
>   - e.g. `mailto:643707+danielrjackson@users.noreply.github.com`
> - **`branch_name`**: The name of the branch where the change was made.
>   - e.g. `main` or a feature branch name.
> - **`version`**: The version of the project that this change applies to.
>   - This should be in the format `X.X.X`, where `X` is a number.
>   - e.g. `0.1.0`
> - **`version_slug`**: A slugified version of the version, suitable for use in file names.
>   - This should be in the format `x-x-x`, where `x` is a number.
>   - e.g. `0-1-0`
> - **`date_time`**: The date and time of the change in the format `YYYY-mm-DDTHH:MM:SS`.
>   - e.g. `20250730T003500Z`
> - **`change_type`**: The type of change (`Deprecate`, `Document`, `Feature`, `Fix`,
>   `Improvement`, `Overhaul`, `Refactor` , `Remove`, or `Security`).
>   - `Deprecate`: A change that marks a soon-to-be-removed feature as to be removed.
>   - `Document`: A change that updates or adds documentation.
>   - `Feature`: A change that adds a new feature or functionality to the project.
>   - `Fix`: A bug fix or issue resolution.
>   - `Improvement`: An improvement to existing code or functionality that does not add new
>     features.
>   - `Overhaul`: A major change that significantly alters the structure or functionality of the
>      project.
>   - `Refactor`: A change that improves the code structure without changing its external behavior
>     or performance.
>   - `Remove`: A change that removes a feature or functionality from the project.
>   - `Security`: A change that addresses a security vulnerability.
> - **`issue_number`**: The issue_number (integer) related to this change, if applicable.
>   - If there isn't a tracking issue or you cannot access it, you can omit this field.
> - **`coverage_percentage`**: The percentage of code coverage after the change.
>   - This should be a number between 0 and 100, representing the percentage of code that is
>     covered by tests.
> - **`file_path`**: The path to the file that has been changed.
>   - You may also use hierarchical paths for section headings, or, if too deep, use bulleted
>     lists. You can do this so that you can group changes within a directory, package, or module
>     together without having to repeat the full path every time. So long as the file is uniquely
>     identified, using this method for referencing files is acceptable.
>   - Path should be relative to the root of the repository.
>   - e.g. `/src/taskautomation/file.ext`
>   - Make one of these for each file that has been changed.
> - **`file_name`**: The name of the file that has been changed.
>   - Within the section for a particular file, you do not need to use the full path if you need to
>     refer to it again. You don't necessarily need to refer to it at all.
>   - If referring to a different file, so long as the name is unique, you can use the minimum
>     specificity need to identify it within this report, so long as it is properly specified at
>     least once.

---------------------------------------------------------------------------------------------------

- **Author**: [{author_name}]
- **Branch**: {branch_name}
- **Version**: {version}
- **Date**: {date_time}
- **Type**: {change_type}
- **Issue Reference**: [#{issue_number}]
- **Coverage**: {coverage_percentage}%

---------------------------------------------------------------------------------------------------

## Description

> [!TIP] A brief description of the change
>
> ***What*** was changed? What does the change do? What is its purpose?

## Rationale

> [!TIP] The reasoning behind the change
>
> ***Why*** was this change made? What problem does it solve, or what benefit does it provide?
> This should include things such as bug fixes, feature additions, or improvements.

## Details

> [!TIP] General details about the change
>
> Include any relevant background information or context.
>
> This should be at the global level for the change, not specifics of individual file changes.

## Files

### `{file_path}`

> [!TIP] Detailed description of changes made to `{file_name}`
>
> Be specific.

## Next Steps

> [!TIP] Expected follow-up actions or considerations
>
> - Testing requirements.
> - Deployment considerations.
> - Documentation updates.
> - Any related tasks or issues to track.

## Mistakes Discovered

> [!TIP] If you discover mistakes caused by previous changes, document them here
>
> This is especially important if you are an AI agent, as it helps track issues that may have
> caused problems in the past.
>
> Make sure to update any of the relevant instructions files (especially the
> [`/docs/guides/lessons_learned.md`](../../guides/lessons_learned.md) file) with any updates that
> would prevent this mistake from being made again.

## Lessons Learned

> [!TIP] Any lessons learned from the change
>
> - What worked well?
> - What was tried that didn't work?
> - What previous changes might have caused an issue?

[//]: # (Links)

[{author_name}]: {author_contact_url}
[#{issue_number}]: https://github.com/danielrjackson/taskautomation/issues/{issue_number}
