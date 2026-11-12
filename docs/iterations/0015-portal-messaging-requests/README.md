# Phase 5B — Patient Messaging & Appointment Requests

[Issue #33](https://github.com/KateK77/careflow-ehr/issues/33) · [Approved Phase 5 prompt](../0014-patient-portal/prompt.md) · [Phase 5A PR #32](https://github.com/KateK77/careflow-ehr/pull/32) · [Preview and UAT](preview-and-uat.md) · [Verification](verification.md)

Branch `phase/0015-portal-messaging-requests` stacks on `phase/0014-patient-portal` at `97772b4deabb61bf5c2a6dd04d77454f0a70eacd`. Phase 5A local regression, Chromium, push CI and PR CI were green before 5B began.

## Design and acceptance

- Patient ownership comes from the linked session. Only an active physician on the patient's eligible appointment history can be selected when opening a thread. The assigned physician alone can use the staff conversation view. Both participants can reply and explicitly mark messages read. Sender, assigned recipient, sequence and timestamp persist.
- A request records a proposed slot or a selected appointment and its captured version. Patient submission only writes portal records. Administrator and FrontDesk use the existing scheduling writer policy to review requests. Approval validates the current appointment, appointment version, conflicts and encounter state through the existing scheduling transaction. Rejection records a response without modifying scheduling.
- Four new models store thread state, messages, requests and command-linked audit events. Migration `portal.0002` is additive. Provider locks coordinate portal writes with scheduling. A command key and fingerprint prevent identical replay from duplicating writes. Stale versions and conflicting review decisions are rejected. A failed audit write rolls back the associated mutation.
- Direct object access, CSRF, read versus write roles, appointment ownership and staff response visibility are covered in the automated suite. Manual acceptance is pending.

## Changed files

The portal adds communication services, views, templates, a migration, Django tests and a Chromium workflow. Portal routes, middleware and navigation integrate the new patient and staff views. The staff base template exposes links only for the relevant staff roles. No clinical or scheduling service changes were required.

## Limitations

This preview has no external delivery or notifications, public registration, clinician coverage handoff, or production identity verification. Threads can become unavailable to the staff side when their assigned physician loses the active Physician role. A conflicting or stale request stays pending for staff review. The application keeps message and audit history append-only through its supported operations. Database administrators retain direct database access. Automated checks do not constitute a production security or accessibility review.
