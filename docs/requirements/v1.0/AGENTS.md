# AGENTS.md — CareFlow EHR workspace rules

You are building CareFlow EHR, an ORIGINAL educational EHR app inspired by common healthcare workflows. This is NOT Epic, and must never imitate official logos/branding or present itself as an Epic product.

## Source of truth
- Read `docs/product-spec.md` before implementing a new feature.
- If the user has kept the spec in the project root, find `01_CareFlow_EHR_完整功能与界面规格.md` and use it instead.
- Distinguish verified public features from our proposed design choices; never infer proprietary internals.

## Critical boundaries
- Use **synthetic/mock patient data only** and mark the product `DEMO — NOT FOR CLINICAL USE`.
- No real clinical decisions, prescriptions, medication administrations, patient records, insurance claims, payments, or external hospital/EHR access.
- No sending patient data to external AI services by default; use a local/mock provider until explicitly authorized.
- Do not claim HIPAA compliance, interoperability certification, production readiness, or Epic affiliation.
- Do not modify anything outside this opened workspace. Ask before destructive migrations, deleting files, secrets, external network integrations, or deploys.

## Development discipline
- Inspect existing files before editing. Preserve user changes and avoid replacing their code unnecessarily.
- Work in small vertical slices: DB model + migration -> API + permission -> UI -> tests -> documentation.
- No non-functional placebo UI; important controls must have real handlers, data, and clear feedback.
- Backend RBAC is mandatory; front-end menu hiding alone does not establish authorization.
- Maintain patient context consistency (`patientId`, `encounterId`); preserve audit trails and signed-note immutability.
- Implement UTC storage and explicit local-time display; handle date, time-zone, and state-transition edge cases.
- Database seeds must be deterministic and synthetic.
- Write automated tests for at least happy path, permission denial, validation, duplicate/conflict handling, and data isolation.

## Response contract
- Before edits: describe precisely what you will change and why.
- After edits: list files changed, commands run, test outcomes, known issues, and next step.
- Never claim tests passed unless you actually ran them.
- Stop at the agreed milestone boundary; ask before starting the next phase.

## Preferred stack
- Next.js/React/TypeScript frontend; FastAPI/Python backend; PostgreSQL with migrations; development fallback as appropriate.
- Accessible original UI; readable components; no oversized monolithic files.
