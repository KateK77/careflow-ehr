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
