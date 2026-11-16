# Next-stage public demo proposal

Status: design proposal only, November 16, 2026. The owner chose screenshots and documentation for this round. No shared credentials, new deployment, account provisioning, paid resources or online database changes are authorized by this document.

## Goal

A recruiter can open the website, start a temporary synthetic demonstration without registration, switch between several staff/patient roles and complete connected workflows. Each visitor receives independent data so one visitor cannot affect another visitor or the existing hosted application.

The current homepage and sign-in routes are reachable. Existing accounts are private, have normal role-specific write permissions and are not safe shared public credentials. No public role login or representative-data verification is claimed in this release. Administrator functions remain screenshot-only until a restricted sandbox design is separately reviewed.

## Options to evaluate

| Approach | Advantages | Constraints |
| --- | --- | --- |
| Separate SQLite database per visitor | Clear data boundary; existing relational workflow models can be reused; reset replaces only one disposable sandbox | Requires safe request-scoped routing, connection cleanup, fixture startup and storage limits; existing free-host capacity is unverified |
| Separate process/container per visitor | Stronger execution boundary; explicit lifecycle | Higher startup/resource cost; no new hosting or charges are approved |
| Shared database with mandatory tenant scope | Potentially lower startup cost | Requires comprehensive tenant-aware models, queries, constraints and audit paths; easy to miss direct-object routes; substantial application changes |
| Read-only shared showcase | Simplest fallback for tours | Does not satisfy the goal of complete independent write workflows |

Prefer evaluating per-visitor disposable databases first for this SQLite prototype, then verify isolation and host capacity before selecting an implementation. No claim is made that the present free PythonAnywhere account can support the target concurrency or a second isolated deployment.

## Proposed visitor journey

1. Choose Start isolated demo. The server creates an unpredictable sandbox identifier and a signed, HttpOnly, Secure session binding. The client never supplies a database filename or existing patient ID as authority.
2. Build a NEW database from a versioned synthetic fixture template. Do not clone the existing hosted database or local previews. Pre-provision fictional patients, appointments, notes, vitals, laboratory and pharmacy prerequisites within that sandbox.
3. Offer explicit role switching for Physician, Nurse, FrontDesk, Lab Staff, Pharmacist and Patient. Resolve the sandbox-local identity on the server; no reusable maintenance password or global user impersonation is exposed.
4. Preserve normal RBAC, patient/encounter relationships, CSRF, signing, version checks and audit events. Switching to a role grants access only to that visitor's sandbox. A full Administrator/superuser account, server administration and host controls remain inaccessible.
5. Show a clear synthetic-demo banner, remaining session lifetime and Reset my demo. Reset affects only that registered disposable sandbox.

## Isolation and reset requirements

- Resolve all authentication, sessions, clinical records, audit events, jobs and cached data inside the same validated sandbox scope. A request must fail closed when scope is absent or mismatched.
- Bind every object request and role selection to the authenticated visitor session. Test copied URLs, cookies, UUIDs, guessed IDs, cross-tab and cross-browser access.
- Store sandbox files in a dedicated directory with a server-side registry. Validate resolved absolute paths and ownership before cleanup; reject symlinks and user-controlled paths.
- Create new files atomically and verify schema/template integrity before exposing them. On reset, close connections, allocate a replacement sandbox and expire the old session. Never overwrite an active shared or existing clinical database.
- Remove only registered expired sandbox artifacts after a safe grace period; preserve short, sanitized operational metrics without storing real visitor data.
- Apply explicit limits on active sessions, request rate, disk use, fixture creation, lifetime and per-sandbox workload. Evaluate queue/deny behavior under saturation.
- Keep payment, prescribing, dispensing and external integrations fictional. No outbound clinical connections or paid AI calls are part of the visitor sandbox.
- Deployment rollback must preserve the current site and database; the existing deployment remains unchanged until a separate migration/deployment plan is approved.

## Acceptance gates before any public launch

Free automated and Chromium tests must show two concurrent visitors with different data, all requested role workspaces, one connected synthetic patient journey, cross-visitor denial on reads/writes, preserved RBAC/CSRF, inability to change another sandbox or maintenance identity, and reset/expiry without affecting other sessions.

Test partially completed requests, signed records, stale tabs, invalid sandbox tokens, cleanup races, restarts, quota exhaustion and recovery. Verify every intended role has representative data and works without registration or published private credentials. Measure actual hosting resource use and identify recurring cost before deployment approval.

## Approval boundary

This proposal is retained for a later implementation decision. The current round publishes only documentation and real screenshots. Do not create accounts, expose existing passwords, deploy services, alter online databases, reset existing data or incur charges under this proposal.
