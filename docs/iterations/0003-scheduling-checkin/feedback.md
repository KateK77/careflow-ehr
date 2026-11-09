# Feedback — Phase 1B

The user approved Phase 1B in the [preserved prompt](prompt.md). The implementation retains Django, existing authentication, patient records and historical documentation.

Implementation decisions are recorded in ADR 0003. Current scheduling access is single-clinic, with physician-only staff limited to their own appointments. States are scheduled, arrived, cancelled and no_show, with clinical progression deferred.

At initial delivery, hands-on acceptance was pending. The dated report below supersedes that status. Prior UX-01–UX-05 items remain deferred as recorded in the Phase 1A feedback.

## Manual user acceptance — reported 2026-11-09

The user reported completing all eleven checks below with passing results and no blocking functional defects. These are user-reported observations, recorded here without an independent rerun of the manual procedures.

| ID | Manual observation reported by the user | Result |
| --- | --- | --- |
| UAT-1B-01 | Created and confirmed a synthetic outpatient appointment | Passed |
| UAT-1B-02 | Appointment appeared correctly on the physician's daily calendar | Passed |
| UAT-1B-03 | Rescheduled the appointment and verified the updated calendar time | Passed |
| UAT-1B-04 | Application rejected an overlapping appointment for the same physician | Passed |
| UAT-1B-05 | The rejected conflicting appointment did not appear in the calendar | Passed |
| UAT-1B-06 | Cancelled an appointment and observed its cancellation event in history | Passed |
| UAT-1B-07 | Rebooked the previously cancelled time slot | Passed |
| UAT-1B-08 | Checked in a synthetic patient and observed Scheduled → Arrived, actor, timestamp and event history | Passed |
| UAT-1B-09 | Refreshed the page and confirmed check-in information persisted | Passed |
| UAT-1B-10 | Physician account viewed its own appointments without edit or cancellation controls | Passed |
| UAT-1B-11 | Physician direct access to an appointment edit URL was denied | Passed |

Manual acceptance is complete for the reported scope. PR #6 remains open for final review and a separate merge decision. [The acceptance documentation request](uat-request.md) preserves the supplied observations and instructions.

## Future non-blocking UI/UX backlog

These are enhancement requests for later evaluation, not confirmed defects, Phase 1B acceptance blockers, or already approved functional changes. Recording them does not authorize implementation in this iteration.

### 1B-UX-01 — Configurable appointment types

Evaluate replacing the free-text Appointment Type field with a controlled list of configurable types, while preserving a free-text visit reason.

### 1B-UX-02 — Compact scheduling filters

Make the filter panel more compact so more of the calendar is visible.

### 1B-UX-03 — Appointment history presentation

Improve responsive layout and column readability, including handling long cancellation reasons.

### 1B-UX-04 — Availability and early check-in policy

Evaluate configurable physician working hours, leave and a reasonable early check-in window as future workflow enhancements. Current behavior remains governed by ADR 0003.

The [Phase 1A UX-01–UX-05 items](../0002-patient-registration/feedback.md) also remain deferred.
