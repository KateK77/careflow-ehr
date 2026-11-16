# CUA-100 v1.0 — actual results

**85/100 native tasks passed (85%). 15 failed. All 100 tasks received a bounded native API attempt; no paid failed task was retried.**

[100 written tasks](tasks.md) · [CSV](results.csv) · [JSON and assertions](results.json) · [Findings](findings.md) · [Offline evidence](offline-rehearsals.json)

## Results by task type

| Group | Passed | Total | Rate |
| --- | ---: | ---: | ---: |
| Entry / reads / authorization (CF-001–070) | 69 | 70 | 98.57% |
| Validation / writes / clinical workflows (CF-071–100) | 16 | 30 | 53.33% |

The aggregate is not a claim that every clinical workflow works autonomously. Read/authorization probes are deliberately reported separately from write tasks.

Three initial launches (CF-002, CF-031, CF-035) were blocked before any API request. Their original JSON is preserved under [preflight evidence](evidence/preflight/). After the port-readiness race was reproduced and fixed offline, each received its first actual paid attempt in a separate evidence directory. The old CF-002 JSON says FAIL; this report explicitly classifies the zero-request browser startup outcome as infrastructure BLOCKED without rewriting it.

The initial launch ledger therefore had **82 PASS, 15 FAIL and 3 pre-API BLOCKED**; the final first-paid-attempt ledger has **85 PASS and 15 FAIL**. This is not retry-adjusted paid success.

## Difficulty breakdown

| Difficulty | Passed | Total | Rate |
| --- | ---: | ---: | ---: |
| 1/5 | 10 | 10 | 100.00% |
| 2/5 | 33 | 33 | 100.00% |
| 3/5 | 26 | 27 | 96.30% |
| 4/5 | 8 | 20 | 40.00% |
| 5/5 | 8 | 10 | 80.00% |

## Verification and usage

- Integrated Django suite: **536 passed**, 94.868 seconds.
- Offline CUA suite after the readiness fix: **44 passed**, 46.420 seconds.
- Task-specific deterministic Chromium rehearsals: **100/100 passed** after test-definition corrections; original failed rehearsals retained privately.
- Post-readiness-fix affected-case preflight: **3/3 passed**.
- Model requested: **gpt-5.4**, official Responses native computer tool with ComputerToolset; OpenAI SDK **3.31.0**, Playwright **1.61.0**.
- Native API requests/responses: **336/336**.
- Measured input/output tokens: **1,279,839 / 12,025**.
- Estimated token cost: **USD 3.379979**. This uses uncached input USD 2.50/million and output USD 15/million; it is not an invoice. Cached-token billing may be lower.
- No automatic paid retries, recharge or changes to application RBAC, CSRF, action restrictions or network boundaries.
- Existing database hash results and final CI links are recorded in the [iteration verification](../../iterations/0030-public-showcase-cua100/verification.md).

Authentication for role-specific tasks was fixture setup through the real login UI, not a claimed model action. Each task used a new temporary synthetic database. The hosted site and existing local databases were not exercised by benchmark writes. Pending native safety approvals remained denied.

## Evidence interpretation

The linked JSON contains actual action types, safe coordinates, observed HTTP navigation, independent assertions, usage and sanitized failure chains. Typed values, passwords, headers and raw request bodies are excluded. Each screenshot is the last successfully captured screen; for a failed case it may precede the failure and is not proof of completion. Full intermediate captures remain in ignored local evidence.

Native execution spanned harness commits 875a406, 672809a, 6187ce8 and 563b5b8. Later records include source hashes; original pilot JSON is preserved with a separate provenance annotation. Application code remained unchanged throughout the benchmark. No manual UAT or comprehensive security claim is made.

## Per-task native outcomes

| Task | Difficulty | Outcome | Requests | Completed actions | Est. USD | Evidence | Last capture |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| CF-001 — Unified landing | 1 | PASS | 3 | 4 | 0.027043 | [JSON](evidence/native/CF-001.json) | [image](evidence/screenshots/CF-001.png) |
| CF-002 — Staff sign-in entry | 1 | PASS | 3 | 4 | 0.026818 | [JSON](evidence/native/CF-002.json) | [image](evidence/screenshots/CF-002.png) |
| CF-003 — Patient sign-in entry | 1 | PASS | 3 | 4 | 0.026728 | [JSON](evidence/native/CF-003.json) | [image](evidence/screenshots/CF-003.png) |
| CF-004 — Patient signup fields | 1 | PASS | 3 | 4 | 0.026982 | [JSON](evidence/native/CF-004.json) | [image](evidence/screenshots/CF-004.png) |
| CF-005 — Staff application fields | 1 | PASS | 3 | 4 | 0.026863 | [JSON](evidence/native/CF-005.json) | [image](evidence/screenshots/CF-005.png) |
| CF-006 — Administrator dashboard | 1 | PASS | 3 | 4 | 0.026802 | [JSON](evidence/native/CF-006.json) | [image](evidence/screenshots/CF-006.png) |
| CF-007 — Physician worklist | 1 | PASS | 3 | 4 | 0.026892 | [JSON](evidence/native/CF-007.json) | [image](evidence/screenshots/CF-007.png) |
| CF-008 — Nursing workspace | 1 | PASS | 3 | 4 | 0.026908 | [JSON](evidence/native/CF-008.json) | [image](evidence/screenshots/CF-008.png) |
| CF-009 — Laboratory worklist | 1 | PASS | 3 | 4 | 0.026787 | [JSON](evidence/native/CF-009.json) | [image](evidence/screenshots/CF-009.png) |
| CF-010 — Pharmacy worklist | 1 | PASS | 3 | 4 | 0.026818 | [JSON](evidence/native/CF-010.json) | [image](evidence/screenshots/CF-010.png) |
| CF-011 — Patient directory | 2 | PASS | 3 | 4 | 0.026818 | [JSON](evidence/native/CF-011.json) | [image](evidence/screenshots/CF-011.png) |
| CF-012 — Patient demographics | 2 | PASS | 3 | 4 | 0.026922 | [JSON](evidence/native/CF-012.json) | [image](evidence/screenshots/CF-012.png) |
| CF-013 — Appointment calendar | 2 | PASS | 3 | 4 | 0.026847 | [JSON](evidence/native/CF-013.json) | [image](evidence/screenshots/CF-013.png) |
| CF-014 — Check-in worklist | 2 | PASS | 3 | 4 | 0.026713 | [JSON](evidence/native/CF-014.json) | [image](evidence/screenshots/CF-014.png) |
| CF-015 — Appointment creation history | 2 | PASS | 3 | 4 | 0.027058 | [JSON](evidence/native/CF-015.json) | [image](evidence/screenshots/CF-015.png) |
| CF-016 — Longitudinal patient chart | 2 | PASS | 3 | 4 | 0.026937 | [JSON](evidence/native/CF-016.json) | [image](evidence/screenshots/CF-016.png) |
| CF-017 — In-progress encounter | 2 | PASS | 3 | 4 | 0.027027 | [JSON](evidence/native/CF-017.json) | [image](evidence/screenshots/CF-017.png) |
| CF-018 — Medical-history empty state | 2 | PASS | 3 | 4 | 0.027072 | [JSON](evidence/native/CF-018.json) | [image](evidence/screenshots/CF-018.png) |
| CF-019 — Longitudinal problems | 2 | PASS | 3 | 4 | 0.026892 | [JSON](evidence/native/CF-019.json) | [image](evidence/screenshots/CF-019.png) |
| CF-020 — Allergy review status | 2 | PASS | 3 | 4 | 0.027103 | [JSON](evidence/native/CF-020.json) | [image](evidence/screenshots/CF-020.png) |
| CF-021 — Medication history | 2 | PASS | 3 | 4 | 0.027043 | [JSON](evidence/native/CF-021.json) | [image](evidence/screenshots/CF-021.png) |
| CF-022 — Encounter diagnoses | 2 | PASS | 3 | 4 | 0.026998 | [JSON](evidence/native/CF-022.json) | [image](evidence/screenshots/CF-022.png) |
| CF-023 — Appointment nursing context | 2 | PASS | 3 | 4 | 0.026908 | [JSON](evidence/native/CF-023.json) | [image](evidence/screenshots/CF-023.png) |
| CF-024 — Longitudinal flowsheet | 2 | PASS | 3 | 4 | 0.026982 | [JSON](evidence/native/CF-024.json) | [image](evidence/screenshots/CF-024.png) |
| CF-025 — Lab catalog | 2 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-025.json) | [image](evidence/screenshots/CF-025.png) |
| CF-026 — Lab order history | 2 | PASS | 3 | 4 | 0.026802 | [JSON](evidence/native/CF-026.json) | [image](evidence/screenshots/CF-026.png) |
| CF-027 — Medication catalog | 2 | PASS | 3 | 4 | 0.026863 | [JSON](evidence/native/CF-027.json) | [image](evidence/screenshots/CF-027.png) |
| CF-028 — Signed medication history | 2 | PASS | 3 | 4 | 0.026832 | [JSON](evidence/native/CF-028.json) | [image](evidence/screenshots/CF-028.png) |
| CF-029 — Billing worklist | 2 | PASS | 3 | 4 | 0.026773 | [JSON](evidence/native/CF-029.json) | [image](evidence/screenshots/CF-029.png) |
| CF-030 — Claims queue | 2 | PASS | 3 | 4 | 0.026863 | [JSON](evidence/native/CF-030.json) | [image](evidence/screenshots/CF-030.png) |
| CF-031 — Radiology worklist | 2 | PASS | 3 | 4 | 0.026908 | [JSON](evidence/native/CF-031.json) | [image](evidence/screenshots/CF-031.png) |
| CF-032 — Imaging catalog | 2 | PASS | 3 | 4 | 0.026683 | [JSON](evidence/native/CF-032.json) | [image](evidence/screenshots/CF-032.png) |
| CF-033 — Inpatient dashboard | 2 | PASS | 3 | 4 | 0.026937 | [JSON](evidence/native/CF-033.json) | [image](evidence/screenshots/CF-033.png) |
| CF-034 — Capacity dashboard | 2 | PASS | 3 | 4 | 0.026877 | [JSON](evidence/native/CF-034.json) | [image](evidence/screenshots/CF-034.png) |
| CF-035 — Emergency tracking board | 2 | PASS | 3 | 4 | 0.026877 | [JSON](evidence/native/CF-035.json) | [image](evidence/screenshots/CF-035.png) |
| CF-036 — Anonymous staff redirect | 3 | PASS | 3 | 4 | 0.027058 | [JSON](evidence/native/CF-036.json) | [image](evidence/screenshots/CF-036.png) |
| CF-037 — Anonymous patient redirect | 3 | PASS | 3 | 4 | 0.026967 | [JSON](evidence/native/CF-037.json) | [image](evidence/screenshots/CF-037.png) |
| CF-038 — Patient denied directory | 3 | PASS | 3 | 4 | 0.027027 | [JSON](evidence/native/CF-038.json) | [image](evidence/screenshots/CF-038.png) |
| CF-039 — Patient denied staff approval | 3 | PASS | 3 | 4 | 0.026892 | [JSON](evidence/native/CF-039.json) | [image](evidence/screenshots/CF-039.png) |
| CF-040 — Patient denied nursing | 3 | PASS | 3 | 4 | 0.027072 | [JSON](evidence/native/CF-040.json) | [image](evidence/screenshots/CF-040.png) |
| CF-041 — Patient denied pharmacy | 3 | FAIL | 3 | 4 | 0.027178 | [JSON](evidence/native/CF-041.json) | [image](evidence/screenshots/CF-041.png) |
| CF-042 — Physician denied registration | 3 | PASS | 3 | 4 | 0.027043 | [JSON](evidence/native/CF-042.json) | [image](evidence/screenshots/CF-042.png) |
| CF-043 — Physician denied demographics edit | 3 | PASS | 3 | 4 | 0.027012 | [JSON](evidence/native/CF-043.json) | [image](evidence/screenshots/CF-043.png) |
| CF-044 — Physician denied account approval | 3 | PASS | 3 | 4 | 0.026998 | [JSON](evidence/native/CF-044.json) | [image](evidence/screenshots/CF-044.png) |
| CF-045 — FrontDesk denied chart | 3 | PASS | 3 | 4 | 0.027072 | [JSON](evidence/native/CF-045.json) | [image](evidence/screenshots/CF-045.png) |
| CF-046 — FrontDesk denied SOAP | 3 | PASS | 3 | 4 | 0.026998 | [JSON](evidence/native/CF-046.json) | [image](evidence/screenshots/CF-046.png) |
| CF-047 — FrontDesk denied history | 3 | PASS | 3 | 4 | 0.027043 | [JSON](evidence/native/CF-047.json) | [image](evidence/screenshots/CF-047.png) |
| CF-048 — Nurse denied SOAP authoring | 3 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-048.json) | [image](evidence/screenshots/CF-048.png) |
| CF-049 — Nurse denied patient creation | 3 | PASS | 3 | 4 | 0.027058 | [JSON](evidence/native/CF-049.json) | [image](evidence/screenshots/CF-049.png) |
| CF-050 — Lab denied demographics | 3 | PASS | 3 | 4 | 0.027072 | [JSON](evidence/native/CF-050.json) | [image](evidence/screenshots/CF-050.png) |
| CF-051 — Lab denied physician worklist | 3 | PASS | 3 | 4 | 0.027058 | [JSON](evidence/native/CF-051.json) | [image](evidence/screenshots/CF-051.png) |
| CF-052 — Pharmacist denied chart | 3 | PASS | 3 | 4 | 0.027072 | [JSON](evidence/native/CF-052.json) | [image](evidence/screenshots/CF-052.png) |
| CF-053 — Pharmacist denied demographics edit | 3 | PASS | 3 | 4 | 0.027058 | [JSON](evidence/native/CF-053.json) | [image](evidence/screenshots/CF-053.png) |
| CF-054 — Billing denied ED | 3 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-054.json) | [image](evidence/screenshots/CF-054.png) |
| CF-055 — Billing denied inpatient | 3 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-055.json) | [image](evidence/screenshots/CF-055.png) |
| CF-056 — Radiology denied SOAP | 3 | PASS | 3 | 4 | 0.027043 | [JSON](evidence/native/CF-056.json) | [image](evidence/screenshots/CF-056.png) |
| CF-057 — HospitalOperations denied approval | 3 | PASS | 3 | 4 | 0.027043 | [JSON](evidence/native/CF-057.json) | [image](evidence/screenshots/CF-057.png) |
| CF-058 — Physician denied unrelated chart | 3 | PASS | 3 | 4 | 0.026937 | [JSON](evidence/native/CF-058.json) | [image](evidence/screenshots/CF-058.png) |
| CF-059 — Mismatched patient encounter denied | 3 | PASS | 3 | 4 | 0.026953 | [JSON](evidence/native/CF-059.json) | [image](evidence/screenshots/CF-059.png) |
| CF-060 — Unclaimed pharmacy details denied | 3 | PASS | 3 | 4 | 0.026982 | [JSON](evidence/native/CF-060.json) | [image](evidence/screenshots/CF-060.png) |
| CF-061 — Own patient dashboard | 2 | PASS | 3 | 4 | 0.026832 | [JSON](evidence/native/CF-061.json) | [image](evidence/screenshots/CF-061.png) |
| CF-062 — Own appointments | 2 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-062.json) | [image](evidence/screenshots/CF-062.png) |
| CF-063 — Own visits | 2 | PASS | 3 | 4 | 0.026922 | [JSON](evidence/native/CF-063.json) | [image](evidence/screenshots/CF-063.png) |
| CF-064 — Own medications | 2 | PASS | 3 | 4 | 0.026773 | [JSON](evidence/native/CF-064.json) | [image](evidence/screenshots/CF-064.png) |
| CF-065 — Released-results empty state | 2 | PASS | 3 | 4 | 0.026953 | [JSON](evidence/native/CF-065.json) | [image](evidence/screenshots/CF-065.png) |
| CF-066 — Own messages | 2 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-066.json) | [image](evidence/screenshots/CF-066.png) |
| CF-067 — Own appointment requests | 2 | PASS | 3 | 4 | 0.026877 | [JSON](evidence/native/CF-067.json) | [image](evidence/screenshots/CF-067.png) |
| CF-068 — Own billing statements | 2 | PASS | 3 | 4 | 0.026863 | [JSON](evidence/native/CF-068.json) | [image](evidence/screenshots/CF-068.png) |
| CF-069 — Owner cannot see unreleased lab result | 3 | PASS | 3 | 4 | 0.026758 | [JSON](evidence/native/CF-069.json) | [image](evidence/screenshots/CF-069.png) |
| CF-070 — Other patient cannot see lab result | 3 | PASS | 3 | 4 | 0.026742 | [JSON](evidence/native/CF-070.json) | [image](evidence/screenshots/CF-070.png) |
| CF-071 — Register synthetic patient | 4 | PASS | 6 | 19 | 0.086010 | [JSON](evidence/native/CF-071.json) | [image](evidence/screenshots/CF-071.png) |
| CF-072 — Required synthetic confirmation | 4 | PASS | 6 | 17 | 0.086005 | [JSON](evidence/native/CF-072.json) | [image](evidence/screenshots/CF-072.png) |
| CF-073 — Duplicate MRN rejection | 4 | PASS | 6 | 18 | 0.085740 | [JSON](evidence/native/CF-073.json) | [image](evidence/screenshots/CF-073.png) |
| CF-074 — Edit demographics and audit | 4 | FAIL | 2 | 2 | 0.015222 | [JSON](evidence/native/CF-074.json) | [image](evidence/screenshots/CF-074.png) |
| CF-075 — Schedule and confirm appointment | 4 | FAIL | 4 | 8 | 0.043143 | [JSON](evidence/native/CF-075.json) | [image](evidence/screenshots/CF-075.png) |
| CF-076 — Check in and audit | 4 | PASS | 3 | 4 | 0.027193 | [JSON](evidence/native/CF-076.json) | [image](evidence/screenshots/CF-076.png) |
| CF-077 — Reschedule same patient | 4 | FAIL | 2 | 2 | 0.015328 | [JSON](evidence/native/CF-077.json) | [image](evidence/screenshots/CF-077.png) |
| CF-078 — Cancel with retained reason | 4 | PASS | 3 | 5 | 0.027050 | [JSON](evidence/native/CF-078.json) | [image](evidence/screenshots/CF-078.png) |
| CF-079 — Create four-section SOAP | 4 | FAIL | 3 | 8 | 0.028270 | [JSON](evidence/native/CF-079.json) | [image](evidence/screenshots/CF-079.png) |
| CF-080 — Sign existing SOAP | 4 | FAIL | 4 | 6 | 0.042405 | [JSON](evidence/native/CF-080.json) | [image](evidence/screenshots/CF-080.png) |
| CF-081 — Complete signed encounter | 4 | PASS | 3 | 3 | 0.026558 | [JSON](evidence/native/CF-081.json) | [image](evidence/screenshots/CF-081.png) |
| CF-082 — Past medical history | 4 | FAIL | 5 | 23 | 0.065128 | [JSON](evidence/native/CF-082.json) | [image](evidence/screenshots/CF-082.png) |
| CF-083 — Active longitudinal problem | 4 | FAIL | 6 | 14 | 0.084208 | [JSON](evidence/native/CF-083.json) | [image](evidence/screenshots/CF-083.png) |
| CF-084 — Document fictional allergy | 4 | FAIL | 5 | 13 | 0.063870 | [JSON](evidence/native/CF-084.json) | [image](evidence/screenshots/CF-084.png) |
| CF-085 — Medication statement | 4 | FAIL | 6 | 27 | 0.088130 | [JSON](evidence/native/CF-085.json) | [image](evidence/screenshots/CF-085.png) |
| CF-086 — Nursing assessment | 4 | FAIL | 3 | 6 | 0.027800 | [JSON](evidence/native/CF-086.json) | [image](evidence/screenshots/CF-086.png) |
| CF-087 — Vital-sign panel | 4 | FAIL | 6 | 16 | 0.085725 | [JSON](evidence/native/CF-087.json) | [image](evidence/screenshots/CF-087.png) |
| CF-088 — Approve pending staff application | 4 | PASS | 3 | 5 | 0.027110 | [JSON](evidence/native/CF-088.json) | [image](evidence/screenshots/CF-088.png) |
| CF-089 — Reject pending staff application | 4 | FAIL | 4 | 8 | 0.042583 | [JSON](evidence/native/CF-089.json) | [image](evidence/screenshots/CF-089.png) |
| CF-090 — Mismatched password confirmation | 4 | PASS | 3 | 10 | 0.028278 | [JSON](evidence/native/CF-090.json) | [image](evidence/screenshots/CF-090.png) |
| CF-091 — Claim signed requisition | 5 | PASS | 4 | 8 | 0.042737 | [JSON](evidence/native/CF-091.json) | [image](evidence/screenshots/CF-091.png) |
| CF-092 — Request clarification | 5 | PASS | 4 | 8 | 0.042857 | [JSON](evidence/native/CF-092.json) | [image](evidence/screenshots/CF-092.png) |
| CF-093 — Approve pharmacy verification | 5 | PASS | 4 | 6 | 0.042202 | [JSON](evidence/native/CF-093.json) | [image](evidence/screenshots/CF-093.png) |
| CF-094 — Record simulated dispensing | 5 | PASS | 4 | 8 | 0.042972 | [JSON](evidence/native/CF-094.json) | [image](evidence/screenshots/CF-094.png) |
| CF-095 — Claim lab requisition | 5 | PASS | 5 | 10 | 0.061940 | [JSON](evidence/native/CF-095.json) | [image](evidence/screenshots/CF-095.png) |
| CF-096 — Collect specimen with identity | 5 | PASS | 5 | 12 | 0.062620 | [JSON](evidence/native/CF-096.json) | [image](evidence/screenshots/CF-096.png) |
| CF-097 — Publish prepared lab report | 5 | PASS | 5 | 8 | 0.061007 | [JSON](evidence/native/CF-097.json) | [image](evidence/screenshots/CF-097.png) |
| CF-098 — Acknowledge exact lab revision | 5 | PASS | 6 | 16 | 0.083985 | [JSON](evidence/native/CF-098.json) | [image](evidence/screenshots/CF-098.png) |
| CF-099 — Compose and sign SOAP journey | 5 | FAIL | 2 | 8 | 0.016328 | [JSON](evidence/native/CF-099.json) | [image](evidence/screenshots/CF-099.png) |
| CF-100 — Schedule and check-in journey | 5 | FAIL | 4 | 8 | 0.043295 | [JSON](evidence/native/CF-100.json) | [image](evidence/screenshots/CF-100.png) |
