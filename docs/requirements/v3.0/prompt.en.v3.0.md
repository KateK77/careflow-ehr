# CareFlow EHR v3.0 implementation prompt — revision 1.0

Status: approved development scope; public operation is not yet provisioned.
Budget: USD 0 per month. Do not open paid plans, spend API credits or incur charges.

This version extends the [v2 source prompt](../../iterations/0028-v2-website/prompt.original.zh.md) and [v2 English translation](../../iterations/0028-v2-website/prompt.en.v1.0.md). Preserve those documents unchanged. The new authoritative instruction and its separate translation are in [iteration 0029](../../iterations/0029-v3-email-access/prompt.original.zh.md).

Build CareFlow EHR 3.0 on the existing Django application, retaining previously implemented clinical and administrative workflows and all historical feedback records.

1. Restore a blue-led professional visual identity. Do not make every component green. Keep meaningful success, warning and error colors.
2. Provide visible patient registration and staff application links on the shared landing and their respective login pages.
3. Bind new accounts to a verified email address. Preserve existing username login. Include expiring verification codes, resend and password recovery.
4. Patient verification must create a separate synthetic patient chart, never claim an existing chart based on email, name or MRN.
5. Staff registration must not grant clinical privileges. Require email verification and an Administrator decision with an explicit role and reason. Do not permit public Administrator or superuser selection.
6. Preserve server-side RBAC, CSRF, patient isolation, signed records, clinical audit trails and optimistic version checks. New auth flows must have bounded request rates and audited transitions.
7. Use additive account migrations only. Test and preview against NEW databases. Leave existing local databases and v2 previews unchanged.
8. Preserve original approved prompts, translations and phase records. Document actual test outcomes in English. Do not call automated checks manual acceptance.
9. Commit/push on a dedicated branch and open a PR; do not merge existing or new PRs without separate approval.
10. Prepare a real Django hosting package so an eventual public website can be linked from GitHub. Do not pretend GitHub Pages runs Django or invent a working hosted URL. Keep repository visibility unchanged.
11. Respect the zero-cost budget. Actual hosting account authentication, a verified sender and deliverable email service must be available before public registration can be claimed operational.
12. Do not deploy real patient data, run paid native CUA calls, create a release, rewrite history or automatically change existing databases.

## Accepted technical interpretation

Email ownership plus the registration password is required to activate a new registration. This avoids unintentionally activating an unsolicited application created with someone else's password. Codes are entered in a CSRF-protected form, not embedded in URLs. New public patients use explicit fictional names, a synthetic MRN and a clearly identified placeholder date of birth. Existing chart-link invitations and authenticated email-address changes are future work.

A free PythonAnywhere account is a candidate runtime, subject to its current limits, account authorization and email connectivity verification. No platform account, sender credentials or public URL has been supplied. Local file-backed email is clearly labeled as a test outbox, not actual external delivery.
