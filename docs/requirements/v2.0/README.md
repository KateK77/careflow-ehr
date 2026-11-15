# CareFlow EHR 2.0 website baseline — revision 1.0

Status: implemented development preview; not a release or manual acceptance.
Source: [original user instruction](../../iterations/0028-v2-website/prompt.original.zh.md), [English translation v1.0](../../iterations/0028-v2-website/prompt.en.v1.0.md).
Issue: [#58](https://github.com/KateK77/careflow-ehr/issues/58).

## Product interpretation

Build a new website presentation using the original CareFlow product and accumulated feedback. Keep the existing Django application, functioning clinical workflows, authentication, permissions, data contracts and audit history. Version 2.0 identifies this website preview; it does not replace the previously released v1.0.0 tag or certify a new clinical product.

The existing [English v1.0 specification](../v1.0-en/README.md) remains authoritative for unchanged business functionality. Original Chinese sources, translations, phase names and prompts remain historical evidence.

## Implemented website

- Original, responsive landing with Staff Portal and Patient Portal entries connected to real authentication.
- Separate staff and patient login presentation with role-neutral guidance, return links and unchanged authentication handlers.
- New staff shell: grouped role-aware navigation, staff identity, current-location highlighting, consistent buttons, panels, forms and tables.
- Actual dashboard counts and clinic-local day's agenda using existing appointment authorization. Pure physicians see their own permitted appointments; the total patient-directory count follows existing directory access. First eight appointments are shown, including cancellations, with a full-schedule link.
- New patient portal shell and dashboard header with an actual appointment-request link. Existing released-result, message, appointment and billing ownership checks remain.
- Registration organized into identity, optional contact details and explicit required synthetic confirmation. Unknown sex is a labeled radio choice. Duplicate confirmation appears only when the backend detects a potential duplicate. No required consent is auto-filled.
- Appointment details, review and confirmation progression. Optional patient search remains visually distinct from required fields.
- Shared responsive styling across the existing physician, history, nursing, laboratory, medication, pharmacy, MAR, billing, imaging, inpatient and emergency screens.
- Fresh-database preview launcher; never reuse or migrate an existing database.

## Feedback disposition

| Historical feedback | V2 treatment |
| --- | --- |
| Disconnected staff/patient entry and inconsistent styling | New public landing, both real login routes, one locally served v2 stylesheet |
| Staff login referred to only four roles | Role-neutral login guidance; all existing roles preserved |
| Directory whitespace and unclear Open labels | Retain compact upstream table, readable MRNs and View Patient actions; new shared design |
| Demographic hierarchy and excessive whitespace | Preserve upstream grouped cards within the new shell |
| Registration field confusion, Unknown sex and confirmation | Explicit section legends, radio choice, required confirmation; keyboard/browser regressions |
| Optional duplicate checkbox confusion | Shown only when actual duplicate review is required |
| Appointment optional search mistaken for booking | Separate collapsed search, clear required fields, explicit review progression; real create/audit verified |
| Narrow responsive tables | Scroll containers and no-page-overflow checks at selected mobile widths; broader device coverage still pending |
| Audit identifiers and dictionary-style previews | Preserve prior readable labels, structured report rendering and append-only evidence; general cross-module label expansion remains deferred |
| Allergy error duplication, encoding, singular units, fictional dose/reference guidance | Preserve existing parent-stack fixes; do not rewrite historical records |
| Native CUA navigation/replay/key failures | Preserve the existing bounded retries, allowlists, approval policies and budgets; offline suite rerun |
| Configurable appointment types, working hours, leave and early check-in policies | Deferred business-scope proposals; not introduced through a redesign |
| Historical long acknowledgement comment | Preserved verbatim in its existing database; no content rewriting |
| New clinical/AI/FHIR/production capabilities | Not invented or represented as delivered by this website increment |

## Acceptance

Both portal links must work; staff and patient isolation must remain enforced on direct URLs and writes. Real registration, appointment confirmation and check-in must preserve database linkage and audit history. Signed clinical records and existing databases must remain unchanged. Static CSS must return successfully, mobile layouts must remain usable, and regression results must be reported as automated evidence rather than manual UAT or native paid acceptance.

## Architecture

A server-rendered Django modular monolith remains. Public/staff/patient v2 templates live under `careflow/core/templates/v2/`; existing template entry points extend them. One local `core/v2.css` defines the visual system; existing navigation and clinical utility JavaScript is reused. No external asset service, framework, package or cloud dependency is introduced.

Dashboard changes are read-only composition using `appointments_for`. There are no model, migration, authentication, role, clinical-service or state-machine changes. Preview fixtures call existing scheduling services to retain valid creation audit events.

Preview users receive new synthetic accounts with a user-supplied password; the launcher binds only to loopback, creates a unique directory for every invocation, and ignores an inherited database path. It never selects existing patient data.

## Limits

This is a local educational prototype. No production security, comprehensive accessibility, clinical validation, new paid CUA acceptance or manual acceptance is claimed. Existing clinical field schemas and state transitions remain unchanged. Version 2.0 is not a release tag. See the [iteration review checklist](../../iterations/0028-v2-website/feedback.md).
