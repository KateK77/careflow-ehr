# V3.1 verification — username/password registration

Execution date: 2026-11-15, America/Chicago. Scope: latest user instruction removes email entirely from signup. Earlier email-draft test logs remain local historical evidence and are NOT the current release counts.

## Actual local results

| Check | Actual result |
|---|---|
| Django system check | PASS, no issues |
| Migration consistency | PASS, no changes detected after the new accounts migration |
| Full Django regression | **530 tests passed**, 93.549 seconds |
| New account/deployment tests | **38 passed** (included in 530, not additional) |
| Complete available Chromium modules | **32 workflows passed**, 115.262 seconds |
| Account Chromium rerun after final readable audit labels | **3 passed**, 4.626 seconds (subset, not additional) |
| Offline CUA suite | **21 passed**, 53.225 seconds |
| Container image build | PASS, Python 3.13 / Gunicorn / WhiteNoise |
| Hosted deployment system check | PASS, no warnings |
| Hosted HTTP/static checks | 6/6 HTTP 200; secure CSRF cookies on form pages |
| Existing protected files | 242/242 SHA-256 unchanged, including 56 SQLite databases |
| Paid native CUA requests | None |
| Manual v3 user acceptance | Not performed/reported |
| Public hosting | Not provisioned |

The full suite comprises the inherited 492 Django tests plus 38 current account/deployment cases. Chromium is a separate explicit module run. The offline CUA suite mocks native responses and rehearses isolated local browser workflows; it is not new paid/live native acceptance. Local worktree CUA tests reuse the root project's installed Django interpreter by an in-process test fixture adapter; source root, network policy and fresh database allocation remain unchanged.

The final readable audit-label change only affects an account template; the three account browser workflows were rerun after it. No clinical logic changed afterward.

## Reproduce

Use the root project's existing Django virtual environment while working in this v3 worktree. Set CAREFLOW_DB_PATH=:memory: for system/migration checks; Django test runners allocate their own isolated test databases.

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput
python manage.py test careflow.accounts --noinput
```

For full Chromium, enumerate all careflow/**/*browser_tests.py modules and pass their dotted names to manage.py test. Use the installed matching Chromium revision at the original .venv/browsers. For CUA, use tools/cua's separate Python environment and its matching browser cache; run unittest discovery for test_*.py with the worktree fixture interpreter adapter described above.

Local detailed logs live outside Git in the root .venv/uat-followup/v3-website-01:
- django-username-final.txt
- chromium-username-final.txt
- cua-username-offline.txt
- docker-username-build.txt
- hosted-username-check.txt
- container-username-http.json
- preservation-username.json

No passwords, local account handoff files, databases, private outboxes or environment files are committed.

## Browser evidence

Browser actions verified patient signup, login, sign-out/re-login and staff access denial; staff signup, inactive-login denial, separate Administrator approval, approved Nurse login and patient-write denial; real portal links, blue CSS, empty unchecked consent, desktop and 390/320-pixel forms. Independent ORM assertions verify account status, patient links, exact role and account audit events.

- [Desktop home](screenshots/v3-home-desktop.png)
- [Patient registration](screenshots/v3-patient-registration-desktop.png)
- [390px form](screenshots/v3-registration-390.png)
- [320px form](screenshots/v3-registration-320.png)

Screenshots show only blank forms, interface artwork or synthetic fixtures; no passwords or verification tokens.

## Corrections during development

The initial email draft was superseded by the user's username-only instruction. No email code remains in the active signup/backend; prior design documents are retained in history.

A negative-password test originally assumed passwordpassword belonged to Django's common-password list. It did not, and the test correctly exposed the incorrect fixture assumption. The fixture now uses password12345, which is rejected by the configured validator. Validation was not weakened.

Windows default text decoding introduced visible mojibake in a draft label and README edit; UTF-8 handling was corrected and the README's exact preimage was retained. No historical source document was changed.

A detached local launcher process initially exited before readiness. The normal hidden subprocess launch succeeded. The launcher itself passed prepare-only and running HTTP checks; no browser timing or application authentication policy was changed to address process setup.

## Hosted simulation

A disposable Docker container used a new tmpfs /data database, no existing volume and no SMTP variables. It applied migrations only to that new QA database, then ran the normal startup checks. Five pages and the hashed v3 CSS returned HTTP 200. Login and signup pages set secure CSRF cookies. Trusted HTTPS proxy headers were simulated on loopback; this does not prove public TLS termination or hosting availability. The QA container was removed afterward.

## Preservation and remaining limits

The before/after manifest covers 56 existing SQLite files plus historical records/debug evidence, 242 files total; all remained unchanged. Original and existing preview databases were never used for tests, migration or seeding. New draft QA databases are left intact; the final local preview uses a separate newly created database.

Original root worktree remains on feature/v2-website at 949a6d74415561070a1bf3e6ccd712b24c1160dc. Local main remains 00c624553cc265e6275a9d2750ab0041a7e6d97f; remote main remains a9e0913b626b88908ad2ca3041d2ec9497ba7d15. No branches, C-drive backups or historical requirements were deleted.

No email recovery exists, by instruction. No publicly accessible site is claimed. Staff approval is a local operator's authorization, not employment verification. Fixed-window rate limits, SQLite capacity, proxy behavior, backups, comprehensive accessibility/security and real deployment operations need additional review. No merge, release, paid API test or paid hosting action occurred.

## GitHub verification

[PR #61](https://github.com/KateK77/careflow-ehr/pull/61) contains implementation [bf8cf41cde748ccb15be1c7f236bd1686cf0add9](https://github.com/KateK77/careflow-ehr/commit/bf8cf41cde748ccb15be1c7f236bd1686cf0add9). The PR tracks actual CI runs for each published head. GitHub CI runs Django checks, the default regression suite and migration consistency; local Chromium and CUA results must not be mislabeled as GitHub checks.

Final whitespace review found one blank line with trailing spaces in the newly added deployment test; it was removed in the traceability follow-up. No executable logic changed.

## Subsequent staff-login feedback

The original results above are retained. The [staff-login follow-up](login-followup.md) adds six regression cases: **536 Django tests and 32 Chromium workflows pass**. It corrects the pending-approval error message without granting access. The user independently confirmed patient signup/login works; pending staff still require Administrator review. See the follow-up for concurrent user database changes and same-database restart evidence.
