# V3 public synthetic-demo deployment

Date: 2026-11-15. Scope: owner-authorized, zero-budget public demonstration.
Tracking: [Issue #60](https://github.com/KateK77/careflow-ehr/issues/60) and [PR #61](https://github.com/KateK77/careflow-ehr/pull/61), stacked on PR #59. No PR was merged.

## Authorization and source

The owner chose free PythonAnywhere hosting, registered account Jiawen, securely authorized the API and opened Bash console 49204071. This implements the publication request preserved in [final-handover.md](final-handover.md). It does not authorize paid upgrades or change repository visibility.

Published URL: **https://jiawen.pythonanywhere.com/**.
Application source: [a9ae1885ee9a98fad6687697db1fcb2581540c75](https://github.com/KateK77/careflow-ehr/commit/a9ae1885ee9a98fad6687697db1fcb2581540c75).
Source ZIP SHA-256: 531429ddbabb313544614676ac797047194319df9180990de062271e03c9b825.
The source archive contains 458 tracked members, excluding databases, local credentials, logs, virtual environments and Git internals.

Python 3.13 / Django 5.2.19 / WSGI / WhiteNoise / SQLite.
DEBUG is false; HTTPS is forced; a new random secret and separate persistent database live outside the source tree.
The platform's newly created default WSGI configuration was backed up before configuring this new application.
No pre-existing remote web application or database was replaced.

## Provisioning and actual verification

Only the NEW remote database was migrated. Initial provisioning created nine staff accounts and two linked synthetic patient accounts. Every account has a different password, delivered privately to the owner. No password is included in this record or public UI.

Remote system/deployment checks, migration consistency, SQLite integrity and foreign-key checks passed.

Nine actual Chromium checks passed on the public HTTPS origin:

1. Homepage returns HTTP 200, both real portal links resolve, and the blue stylesheet is applied.
2. Referenced stylesheets return HTTP 200.
3. Homepage fits a 390-pixel mobile viewport without horizontal overflow.
4. Provisioned patient signs in; staff-application administration returns HTTP 403.
5. A newly registered synthetic patient signs in immediately with its chosen password.
6. A newly registered Nurse applicant remains inactive and receives approval-pending login guidance.
7. Administrator signs in and approves that applicant with an explicit role and reason.
8. The approved Nurse signs in; restricted patient creation returns HTTP 403.
9. Session and CSRF cookies are Secure; the session cookie is HttpOnly.

These are scripted Chromium deployment checks, not native paid CUA or new user-reported manual UAT. No paid API calls were made.
An initial browser invocation used the wrong installed-browser directory; the verified run used the existing project Chromium installation. A verification-only exact label selector was corrected to the actual password input ID. Neither required an application change.
Initial exploratory requests to incorrect guessed login/static paths returned 404; actual application-linked routes and assets passed.

Independent server-side assertions confirmed the QA patient's registration event, the QA Nurse's single approval event, active status and Nurse role.
Final verification snapshot: 13 users and 3 synthetic patients (including the two deployment QA accounts). SQLite integrity was "ok"; foreign-key errors: zero.

A SQLite online backup was restored to a separate new verification file. Integrity and user counts passed; the active database hash did not change during backup verification.
The public runtime uses persistent host storage. Automated periodic backups and ongoing monitoring are not configured.

## Evidence and preservation

Owner-private evidence directory: .venv/uat-followup/pythonanywhere-jiawen in the official local repository:
- browser-evidence/results.json: nine PASS records.
- browser-evidence/public-home-desktop.png and public-home-mobile.png.
- browser-evidence/public-staff-pending.png: login input values cleared before capture.
- remote-verification.json: database/role/audit/backup assertions.
- local-preservation.json: all 62 pre-existing local SQLite files retained identical SHA-256 hashes across public-browser verification.
- PUBLIC-WEBSITE-ACCOUNTS-PRIVATE.txt: private owner credentials, deliberately excluded from Git.

The earlier local regression evidence remains 536 Django tests and 32 Chromium workflows, not rerun or relabeled as public-host comprehensive testing. [Application evidence](verification.md) and [login follow-up](login-followup.md) remain unchanged. Historical source prompts, earlier records, local preview databases, signed notes and development branches are preserved.

## Visitor rules and limits

Share the website URL, not a localhost address or private repository link.
Patients register with username/password/confirmation and can sign in immediately.
Staff register and wait for Administrator approval; public signup never grants Administrator.
No email address or email recovery is required or available.
The owner receives demonstration passwords privately; do not publish administrator credentials.

The repository remains private. PR #61 and its parent remain unmerged. The hosted application is an authorized branch snapshot, not a new release tag or clinical production deployment.

Free-host quotas, one worker, shared-proxy rate limits and periodic renewal affect availability. The owner must renew the free application as required by PythonAnywhere and monitor storage. Concurrent load, all clinical workflows, exhaustive RBAC/security/accessibility and disaster recovery procedures were not comprehensively retested on the public host. The public database starts with basic fictional accounts/charts, not copied historical clinical scenarios.

**DEMO — NOT FOR CLINICAL USE. Synthetic data only.**
