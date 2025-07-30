# Change Guidelines

> [!CAUTION] Before You Start
>
> Please read these guidelines before contributing.
>
> These guidelines are designed to help you contribute effectively and efficiently.
>
> - Failure to do so may result in your contribution being rolled back or rejected.
> - You don't want to waste your time or ours.

> [!WARNING] Check the Lesson Learned Section
>
> The [Lessons Learned] section in this document has important information about the project that
> was learned the hard way. Read it so you don't make the same mistakes.

## Tasks

> [!IMPORTANT] Check the Task List or Issues
>
> Before starting work on a new feature or bug fix, check the task list or issues to see if it has
> already been reported or if someone else is already working on it.
>
> Select the first uncompleted task on the list and complete it.

> [!IMPORTANT] One Change at a Time
>
> Please submit one change per pull request. These can be found in [`/docs/TASKS.md`] or the issues
> tracker.

> [!WARNING] Add Tasks When Needed
>
> If you discover an issue or task or bug that needs to be addressed, please add it to the
> [`/docs/TASKS.md`] file or the issues tracker. Do not slip it into the feature or bug fix you are
> working on. This helps keep the project organized and makes it easier for others to contribute.
>
> It also makes rollbacks easier if something goes wrong, as the change is isolated to a single
> commit.

> [!IMPORTANT] Consider Requirements When Adding New Tasks
>
> When adding new tasks to the [`/docs/TASKS.md`] file or the issues tracker:
>
> - Check if any existing tasks either depend on the new task or are prerequisites for it.
>   - If so, be sure to link the tasks together appropriately.
> - This will help prioritizing the tasks and ensure that they are completed in the correct
>   order.

## General Guidelines

> [!IMPORTANT] Use Existing Code
>
> If possible, use any existing code in the project to implement the feature.
> It's especially useful to check the libraries to see if they already have the functionality you
> need.

> [!IMPORTANT] Remember Security
>
> If you are making changes that affect security, please be sure to follow best practices.
> Double check that you are not introducing any security vulnerabilities.
>
> If you see any security vulnerabilities, be sure to add them to the [`/docs/TASKS.md`] file or the
> issues tracker as high priority issues.

## Coding Standards

- PEP8
- Functions over classes except in tests
- Use double quotes around strings that are used for interpolation or that are natural language
    messages
- Use single quotes for small symbol-like strings (but break the rules if the strings contain
    quotes)
- Use triple double quotes for docstrings and raw string literals for regular expressions even if
    they aren't needed.
- Example:

    ```python
    LIGHT_MESSAGES = {
        'English': "There are %(number_of_lights)s lights.",
        'Pirate': "Arr! Thar be %(number_of_lights)s lights."
    }
    def lights_message(language, number_of_lights):
        """Return a language-appropriate string reporting the light count."""
        return LIGHT_MESSAGES[language] % locals()
    def is_pirate(message):
        """Return True if the given message sounds piratical."""
        return re.search(r"(?i)(arr|avast|yo ho ho)!", message) is not None
    ```

> [!IMPORTANT] Specify Parameter Types
>
> When possible, specify the types of parameters in function signatures.
>
> - This helps with code readability and understanding how to use the function.
> - It also helps static analysis tools catch potential issues.
> - The IDE can also show the parameter types when hovering over the function.

> [!IMPORTANT] Follow the Code Style
>
> Please follow the code style of the project.
> This includes things like indentation, line length, and naming conventions.
>
> The line length used in this project is 99 characters.

> [!IMPORTANT] Prefer Dry Code
>
> Avoid duplicating code.
> If you find yourself copying and pasting code, consider refactoring it into a function or
> class.

> [!IMPORTANT] Use Meaningful Names
>
> Use meaningful names for variables, functions, and classes.
> This helps make the code more readable and understandable.
>
> - Avoid using single-letter variable names except for loop counters or classical variable names
>   like `i`, `j`, `k`, or `x`, `y`, `z`. If it fits a standard scientific or mathematical formula,
>   then it's okay. But add docstrings to explain what the variable is for in case someone else
>   isn't familiar with the formula.
> - Avoid using abbreviations or acronyms unless they are well-known and widely used.
> - Use descriptive names that convey the purpose of the variable, function, or class.
> - Use consistent naming conventions throughout the codebase.
> - When possible, use names that are self-explanatory and do not require additional comments to
>   understand.
> - Avoid generic names like `data`, `info`, or `temp` unless they are used in a very specific
>   context where their meaning is clear.
> - Consider the length of the name, balancing between being descriptive and concise.

> [!IMPORTANT] Raise Issues if Code Is Atypical
>
> If you see code that is atypical or does not follow widely accepted conventions, please raise an
> issue or comment. A good location for this is in `/docs/notes`.
>
> If a convention is common for a certain type of code, such as AI/ML code, then follow the widely
> accepted conventions for that type of code. Be sure to add documentation explaining what is going
> on and why it is done that way, especially for domain specific code.

## Documentation

> [!IMPORTANT] Include Documentation
>
> Documentation is important for understanding the code and how to use it.
>
> The important part of documentation is the ***WHY***, not the ***WHAT***.
>
> - The code itself is the ***WHAT***, and it should be clear from the code what it does.
> - We're looking for context so that we can understand why the code was written the way it was and
>   what purpose it serves.
>
> Add docstrings to functions, classes, modules, and even variables.
>
> - This helps others understand the code and how to use it.
> - It also helps because then the IDE can show the documentation when hovering over the code.

> [!IMPORTANT] Update Documentation
>
> If documentation is out of date, please update it. Incorrect documentation is worse than no
> documentation at all.

> [!WARNING] Avoid Removing Documentation
>
> Avoid removing or drastically abbreviating documentation.
>
> Unless there is a compelling reason to do so, the documentation was probably put there for a
> reason.

## Finishing Up Your Change

> [!IMPORTANT] Check Diffs Before Committing
>
> Before committing your changes, check the diffs to ensure that you are only committing the
> changes you intended to make.
>
> - Look for any unintended or unnecessary changes that may have been made.
> - Check for code that may have been accidentally modified or removed.

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

### Change Report Instructions

Record your contributions in the `/docs/changelog` folder.

Use the [template] at `/docs/templates/changelog/CHANGELOG_ENTRY_TEMPLATE.md` to create a new change report.

Filenames must follow `main_<version_slug>_<datetime_slug>.md` (e.g., `main_0-1-0_20250730T123500Z.md`).

### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. The pull request should be contained:
   - If it's too big consider splitting it into smaller pull requests.
3. If the pull request adds functionality, the docs should be updated.
   - Put your new functionality into a function with a docstring, and add the feature to the
     list in README.md.
4. The pull request must pass all CI/CD jobs before being ready for review.
5. If one CI/CD job is failing for unrelated reasons you may want to create another PR to fix that
    first.

---------------------------------------------------------------------------------------------------

## See Also

- [Authors]
- [Changelog]
- [Contributors] [^1]
- [Tasks]
- [Testing]

---------------------------------------------------------------------------------------------------

[//]: # (Links)

[`/docs/TASKS.md`]: ../TASKS.md
[Testing]: #testing
[Lessons Learned]: #lessons-learned
[template]: ../templates/changelog/template.md
[Authors]: AUTHORS.md
[Changelog]: CHANGELOG.md
[Contributors]: ai_assistants.md
[Tasks]: task_instructions.md
[AI Assistants]: ai_assistants.md#ai-assistants

<!-- Footnotes -->

[^1]: *See [AI Assistants] for a list of AI assistants that contributed to this project.*
