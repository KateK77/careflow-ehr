# Codex development guide — original proposal

English translation revision 1.0.0, dated 2026-11-07. Source package v1.0. [Original guide](../v1.0/codex-prompts.md) · [Translation registry](README.md).

Read the complete specification supplied as `01_CareFlow_EHR_完整功能与界面规格.md` or `docs/product-spec.md` before the initial task. Implement, test and accept one phase at a time.

## Historical setup instructions

1. Open a separate empty project folder in VS Code, for example `D:\AI-Workspace\Personal\careflow-ehr`, outside existing MedAgentBench or RAG projects.
2. Place the full specification and AGENTS.md there, using docs/product-spec.md if appropriate.
3. Open the Codex sidebar in that folder and submit the first prompt.
4. First request environment inspection and phased planning without code creation. Review that response before implementing Phase 0.

The following prompt bodies were already English in the source and are reproduced verbatim. They describe the historical starting proposal. Current approved architecture decisions govern the existing Django project.

## Prompt 1 — Analyze requirements and propose a development plan

```text
You are my senior full-stack software engineer and technical lead. We are building an ORIGINAL, educational, demo-only healthcare EHR called CareFlow EHR, inspired by common EHR workflows, NOT an exact Epic software clone.

Read docs/product-spec.md and AGENTS.md completely, then inspect the current workspace and local environment before proposing any code changes.

Goals:
- A working multi-role EHR with synthetic patients: registration, scheduling, patient chart, ambulatory visit, notes, diagnosis, orders, laboratory results, inbox, and later nursing/inpatient/portal and AI-assisted chart review.
- Modern original UI: desktop clinical workspace with global header, navigation, patient context sidebar, task-oriented main area, contextual drawers, role-based dashboards, and a separate patient portal.
- All core actions must persist to a backend and database. NO fake buttons, no static-only prototypes marketed as functional.
- Demo/synthetic data only. Display a clear NOT FOR CLINICAL USE label. No real prescriptions, payments, PHI, real EHR integrations, or claims of compliance/certification.

Preferred stack: React/TypeScript/Next.js frontend; Python/FastAPI backend; PostgreSQL plus SQLAlchemy/Alembic; use a SQLite fallback only if local Docker isn't available. Tests with Pytest and Playwright when feasible. Propose changes if necessary and explain why.

IMPORTANT FOR THIS FIRST TURN:
1. Do NOT create, delete, or modify any files yet.
2. Inspect the existing folder, operating system, runtime versions, Docker/Git/Node/Python status, and available project files. Do not touch unrelated projects.
3. Summarize all major modules and identify gaps/ambiguities in the product spec.
4. Propose an incremental milestone plan, emphasizing an end-to-end functional vertical slice instead of generating every screen at once.
5. Show the exact Phase 0 file/folder structure and commands you intend to run.
6. Explain the risks, dependencies and acceptance tests.
7. STOP and ask me to approve the Phase 0 implementation plan before writing code.

Work in small, inspectable, testable steps. At every completed step report files changed, how to run, tests actually run, remaining issues, and the next proposed step. Never claim a test passed unless it was executed.
```

## Prompt 2 — Submit after approving the plan

```text
I approve the Phase 0 plan, with these constraints:
- Work only inside the currently opened CareFlow EHR project workspace.
- Create the monorepo, minimal running frontend/backend, migrations, synthetic seed data, simple demo login, role-based route protection, and an original app shell with the demo warning.
- Build and test one working path end to end: demo user signs in -> opens dashboard -> opens a real patient list from API -> opens a patient snapshot from database.
- Do not build appointments, notes, lab, pharmacy, patient portal, or AI yet.
- Do not delete files or modify unrelated projects. Use mock clinical data only.
- Add README with exact commands and .env.example. Run lint/typecheck/API tests where possible and report their real results.
- When done, STOP and wait for my review before Phase 1.
```

## Evaluation checklist

- Did Codex read the requirements and verify the workspace and environment first?
- Did it divide the broad specification into testable phases?
- Did it distinguish public Epic features, proposed project designs and future functionality?
- Did it create real database/API behavior instead of hardcoding patients in frontend JSON?
- Did it provide run instructions, actual test results, screenshots or a reachable local URL?
- Did it propose alternatives for Docker/version limitations while preserving safety and testing?
- Did it stop at the first agreed review boundary?

## Implementation sequence

- Phase 0 provides a running foundation, login and patient list.
- Phase 1 adds appointments, registration, check-in and the patient snapshot.
- Phase 2 adds vitals, allergies, medication reconciliation, diagnoses, SOAP notes and signatures.
- Phase 3 connects orders, laboratory release and Inbox review to complete the outpatient flow.
- Phase 4 adds pharmacy review, nursing MAR, inpatient, emergency and imaging.
- Phase 5 adds the portal, billing simulation, population analysis and demonstration standard interfaces.
- Phase 6 adds cited AI summaries/note drafts, quality work and demonstration deployment.

Each phase requires the user's manual acceptance and a Git commit before continuing.
