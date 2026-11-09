# Feedback and changes

2026-11-06 — The user approved Phase 1A Patient Management after Phase 0 merged. The effective prompt is preserved separately.

Implementation decisions made within the approved scope are documented in ADR 0002. Administrator and FrontDesk may maintain demographics, Physician and Nurse may read them. Potential duplicate identities require confirmation. Concurrent stale edits return a conflict without overwriting the newer version.

At initial delivery, hands-on acceptance was pending. The dated record below supersedes that status.

## Manual user acceptance — reported 2026-11-08

The user reported completing the checks below against the Phase 1A application and stated that every check passed. These are user-reported manual observations. They were not independently repeated as part of this documentation update.

| ID | Manual check reported by the user | Result |
| --- | --- | --- |
| UAT-01 | Administrator authentication | Passed |
| UAT-02 | Patient directory and MRN search | Passed |
| UAT-03 | Patient detail view | Passed |
| UAT-04 | Synthetic patient registration | Passed |
| UAT-05 | Patient demographic editing and persistence | Passed |
| UAT-06 | Creation and update audit events displayed in the UI | Passed |
| UAT-07 | Duplicate MRN rejection | Passed |
| UAT-08 | Physician login and read-only patient access | Passed |
| UAT-09 | Physician editing denied through direct URL access | Passed |
| UAT-10 | Physician registration denied through direct URL access | Passed |

No blocking functional defects were reported in these checks. Functional acceptance for the listed Phase 1A scope is complete. PR #4 remains open for final review and a separate merge decision.

## Future UI/UX backlog — non-blocking

The user supplied the following feedback from manual acceptance discussions in ChatGPT. These are future enhancement requests, not confirmed defects or Phase 1A acceptance blockers. Their recording does not authorize implementation or start Phase 1B.

### UX-01 — Patient directory information density

- Reduce excessive row height and whitespace.
- Improve table readability and information density.
- Consider patient status and most recent encounter date in future phases.

### UX-02 — Patient detail layout and information hierarchy

- Improve the organization and visual hierarchy of demographics.
- Reduce excessive whitespace.
- Prepare the layout for future medical history, medications, allergies, encounters and laboratory results. Those clinical sections remain outside Phase 1A.

### UX-03 — Navigation and button labels

- Consider clearer alternatives to ambiguous labels such as Open, including View Patient or View Chart according to the actual destination.
- Use consistent navigation and button terminology across the application.

### UX-04 — Registration and editing forms

- Improve field labels, grouping and input guidance to reduce accidental entry into incorrect fields.
- Review mandatory synthetic-data confirmation checkbox usability while preserving necessary safety safeguards.
- Retain clear validation messages for missing fields, duplicate MRNs and invalid input.

### UX-05 — Audit history presentation

- Improve the readability of registration and update events.
- Clearly show event type, actor, timestamp and changed fields.
- Evaluate additional change-history detail without unnecessarily exposing sensitive information.

[Acceptance documentation request](acceptance-request.md) records the instructions for this follow-up. The [verification record](verification.md) distinguishes manual observations, automated evidence and behaviors outside the acceptance evidence.
