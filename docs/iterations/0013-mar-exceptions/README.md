# Phase 4B-2 — MAR Exceptions, Corrections & Chart Integration

[Issue #29](https://github.com/KateK77/careflow-ehr/issues/29). Stacked on verified 4B-1 commit `e679bf9d529e4b04f9580149b6fa0c3cc86850ba`. The [approved prompt](../0012-nurse-mar/prompt.md) covers both increments.

A pending task may be administered, held, refused or omitted. Held is an intermediate state. A Nurse can resolve it as administered, refused or omitted in the same active Encounter. Administered, refused and omitted are terminal for ordinary recording. A Nurse may explicitly correct a recorded outcome during an active Encounter with an explanation. A correction adds a revision and never erases the original event. A correction to Held permits a later resolution. The effective state is the highest revision.

Exception outcomes require a fictional reason and carry no administration quantity. Administration uses the full receipt quantity. All events record an actual simulated event time and a separate audit recording time. Corrections may amend an inaccurate event time within the original time bounds. Completed Encounters allow history only. Phase 4A late pharmacy processing continues independently.

Manual UAT is consolidated after both increments. See [acceptance.md](acceptance.md).
