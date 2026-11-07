# CareFlow EHR development rules

CareFlow EHR is an original educational prototype inspired by common EHR workflows. Use synthetic data only and label application screens DEMO — NOT FOR CLINICAL USE. Do not claim clinical readiness, certification, or Epic affiliation.

## Before changing code

- Read [the current requirements baseline](docs/requirements/README.md), [architecture](docs/architecture.md), and the current Issue and iteration record. If instructions conflict, document the conflict and confirm the scope before implementing it.
- Extend the existing Django project in small, testable increments. Preserve working behavior and user changes. Obtain explicit approval for destructive migrations, feature removal, external integrations, or deployment.
- Keep credentials, patient information, local databases, caches, original archives, and sensitive logs outside Git. AI uses a local or mock provider by default.
- Enforce access on the backend. Preserve patient and encounter context, auditability, signed-note immutability, and UTC storage with explicit local-time display as applicable.

## Delivery and review

- Follow Issue → Branch → Commit → PR → Review → Merge. Work from the approved base on a branch dedicated to the issue. Link the PR and iteration record to the issue.
- Run checks appropriate to the changes. For feature slices, cover success, permission denial, invalid data, conflicts, and data isolation where applicable.
- Record the effective prompt, user feedback, decisions, files changed, commands and actual results, known gaps, and acceptance outcome. Use the [iteration template](docs/iterations/TEMPLATE.md).
- Wait for human review and acceptance before merging or beginning the next milestone.

## Mandatory documentation language and historical preservation

- Follow [language policy v1.0](docs/policies/language/v1.0/README.md). Preserve original Phase 0 requirements and records, including Chinese documents, as immutable history.
- Write all new GitHub Issues, PRs, commit messages, requirements, technical documents, reports, feedback summaries and acceptance records in professional English.
- Read and maintain the [English requirements baseline](docs/requirements/v1.0-en/README.md) alongside its authoritative original sources and approved architecture decisions. Every translation must identify its source version, translation revision and original-document link.
- Preserve approved prompts verbatim. For Chinese prompts, add a separate, accurately translated English file. Translate Chinese user feedback and instructions into English for GitHub documentation while preserving the original source.
- Keep source documents and translations linked through the versioned registry. Record translation corrections as a new revision and substantive requirement changes as a separately approved source version.
- Apply this policy through documentation changes. Application behavior changes require their own approved scope.
