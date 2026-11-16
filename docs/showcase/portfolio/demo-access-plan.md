# Public demo account availability and approval plan

Status: proposal only. No new accounts, deployment, passwords, permissions or online database records have been changed for this portfolio update.

## Current verified access

The live homepage, staff sign-in and patient sign-in routes returned HTTP 200 on November 16, 2026. This confirms route availability, not successful authentication or representative data for every role.

Prior deployment evidence records private, uniquely passworded staff and patient accounts. These are not approved public shared credentials. The existing Administrator can approve staff enrollment; Physician, Nurse, FrontDesk, Lab Staff and Pharmacist roles have genuine synthetic workflow write access. The application currently has no verified per-account public read-only mode or automated reset lifecycle.

No public shared account is therefore listed as usable, and no private credential is disclosed. Administrator access is screenshot-only. All seven requested shared-role login/feature checks remain BLOCKED on safe provisioning approval.

## Proposed safe next increment (requires separate approval)

1. Provision a separate demonstration instance/database from NEW synthetic fixtures, without importing or replacing the current hosted or local databases. Verify hosting capacity and cost before selecting a deployment; no paid infrastructure is authorized.
2. Add a server-enforced public-demo read-only boundary for dedicated shared accounts. Preserve role/patient scoping and CSRF. Permit only the minimum login/logout operations; deny clinical/admin mutations, credential changes, account creation/review and privilege elevation for shared sessions. Hiding buttons is insufficient.
3. Keep maintenance Administrator/superuser identities private and separate. Public role accounts must not be staff/superusers for Django administration. Start with read-only Physician, Nurse, FrontDesk, Lab Staff, Pharmacist and one linked Patient; use administrator screenshots.
4. Populate fictional charts, appointments, notes, vitals, lab results and pharmacy records using dedicated test fixtures. Generate separate new passwords that have never been used for development, hosting or the owner's private accounts.
5. Back up and integrity-check the new fixture database before release. If a future write sandbox is approved, allocate a fresh database per visitor/session or replace only an explicitly identified disposable sandbox from its immutable seed; never reset the existing persistent database.
6. Verify every login, correct workspace, one representative read, cross-role/patient isolation and direct write denial with free browser tests. Verify passwords cannot be changed and server administration is inaccessible. Only then publish actual verified shared credentials in the README.

The read-only boundary is additional implementation/deployment work, outside this documentation-only approval. It must not be implemented implicitly here. The current website can remain unchanged while this proposal is reviewed.

## Risks and remaining decisions

Shared writable accounts let visitors affect each other's records and audit identities. Read-only access mitigates clinical data mutation but still needs session/rate-limit/storage management. Existing free-host single-worker/quota limits and the capacity for a second isolated instance need verification; zero additional cost is not assumed.

Approval needed: whether to undertake the isolated read-only shared-demo increment, including its explicit account provisioning and hosting plan. Until then, retain screenshots and optional individual patient signup as the honest available experience.
