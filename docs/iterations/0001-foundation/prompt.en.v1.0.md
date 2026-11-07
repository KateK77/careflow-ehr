# Approved Phase 0 prompt — English translation v1.0

Translation revision 1.0.0, dated 2026-11-07. Source record version 1.0. [Verbatim Chinese original](prompt.md) · [Translation registry](../../requirements/v1.0-en/README.md).

The CareFlow EHR migration to the D drive has passed acceptance.

I formally approve Phase 0, covering the project documentation system and GitHub development workflow.

Official project directory is `D:\AI-Workspace\Personal\careflow-ehr`. GitHub repository is `KateK77/careflow-ehr`.

Perform the following tasks on the existing Django project.

## 1. GitHub iteration management

- Create the development branch phase/0001-foundation from main.
- Create a Phase 0 GitHub Issue documenting requirements, scope and acceptance criteria.
- Preserve the existing Git history and project initialization.

## 2. Complete development traceability

Establish a suitable documentation structure under docs covering product requirements and specification versions, original prompts for each iteration, user feedback and change requests, software architecture and technical decisions, development reports, and test/acceptance results.

Each iteration must be traceable to its GitHub Issue, commits and PR.

## 3. Organize the Epic-inspired EHR product specification

Read the existing requirements on the D drive. Establish them as the formal version-controlled baseline for future development.

- Preserve the original ZIP and extracted documents.
- Preserve the existing root README.md and AGENTS.md.
- Use a suitable separate directory for specification files whose names conflict with existing project files.
- Exclude local databases, caches, keys and sensitive files from GitHub.

## 4. Long-term development rules

Extend AGENTS.md and CHANGELOG.md. Require future iterations to develop incrementally on the existing software, preserve working functionality, read current requirements before development, run relevant tests afterward, record changed files/test results/user feedback/outstanding issues, and follow Issue → Branch → Commit → PR → Review → Merge.

## 5. Complete Phase 0

1. Inspect the Git diff.
2. Run tests or static checks appropriate to this phase.
3. Commit the changes on the development branch.
4. Push to GitHub.
5. Create a PR linked to the Phase 0 Issue.
6. Report changed files, commit SHA, test results, and Issue/PR links.

Preserve existing clinical business logic, the database and the C-drive backup. Do not automatically merge into main, create a formal Release, or commit real patient data.

Stop after Phase 0 and wait for my review and acceptance before Phase 1.
