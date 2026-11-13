# Iteration 0027 — Unified workspace upgrade

- Issue: [#56](https://github.com/KateK77/careflow-ehr/issues/56).
- Branch: `ui/unified-workspace-upgrade`.
- PR: [#57](https://github.com/KateK77/careflow-ehr/pull/57), targeting PR #55.
- Implementation: [81cbc2b2e9b97513c5adf539912fdcd29ad735a2](https://github.com/KateK77/careflow-ehr/commit/81cbc2b2e9b97513c5adf539912fdcd29ad735a2).
- Base: `fix/appointment-form-guidance`, PR #55, commit `214a309f52af642b4c59be85f3bc7ec646766815`.
- Main integration reference: `a9e0913b626b88908ad2ca3041d2ec9497ba7d15`, PR #47.
- Original approval and translation: [prompt](prompt.md).
- Versioned scope and feedback: [feedback](feedback.md).
- Actual test evidence: [verification](verification.md).
- Requirements: S01–S05, S07 and applicable existing workflow presentation; original [English baseline](../../requirements/v1.0-en/README.md).
- Human acceptance: pending.

## Decisions

Reuse the existing server-rendered architecture, shared permission context, clinical display filters and native CUA driver. Add presentation assets rather than modify clinical services, models, migrations, roles, authentication or workflow state rules.

The open stack is #49 → #51 → #52 → #53 → #54 → #55 → this upgrade. This branch contains the current upstream improvements; do not merge it directly into main without separately reviewing the stack and integration plan.

Keep the pre-existing untracked `debug.log` out of the commit. No application database is used for tests. Preserve local main and every existing development branch.

## Development report

- Shared compact workspace styling and active navigation with progressive enhancement.
- Role-gated dashboard cards linking only to existing authorized routes.
- Lab Staff identity and brand destination fixed without widening permissions.
- Patient directory and demographic hierarchy improved.
- Human-readable registration and appointment audit labels; stored history unchanged.
- Appointment filter context remains visible after searching; required form/action fit verified at laptop size.
- Allergy retry errors displayed once while retaining posted choices and explicit confirmation.
- Staff/patient login return links and patient portal navigation styles.
- Existing browser selectors updated for already-introduced radio and optional-search disclosure.
- Added targeted Django and Chromium regressions. CUA visible-label expectation updated; database verifier and action policies unchanged.

## Historical preservation

[Baseline current-document snapshots](baseline-current-documents/) retain exact pre-update bytes of README, roadmap and project-status. Original requirements, translations, approved prompts and earlier iteration evidence are not rewritten.

No phase is renamed. New clinical modules, changes to appointment types/hours, new timing restrictions, expanded identity resolution, production deployment and paid API testing are outside this increment.

## Screenshots

Offline synthetic fixtures only, with no credentials visible.

- [Staff workspace](screenshots/staff-workspace-1280.png)
- [Appointment form at 1280x800](screenshots/appointment-1280-initial.png)
- [Patient directory at 390px](screenshots/directory-390.png)
- [Patient portal at 390px](screenshots/patient-portal-390.png)

Archived current-document snapshots preserve source bytes; their relative links retain their original repository locations rather than this archive directory.
