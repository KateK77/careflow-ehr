# Automated verification — Phase 3B-2

Manual acceptance: deferred, not performed by the agent.

- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: no changes.
- `python manage.py test --noinput`: **211 tests passed**, including 194 parent tests and 17 new processing tests.
- Chromium gate: all nine workflows passed (new processing plus eight parent workflows). No manual UAT is inferred from Chromium.
- Coverage includes identity mismatch, invalid JSON/decimal/unit/context, post-completion signed SOAP preservation, receipt-ever cancellation, rejection/recollection, direct role denials, CSRF, replay/stale versions, audit rollback, concurrent lab claims, receipt/cancellation and duplicate publication races.
- New `labs.0002` changes lab tables only: LabResult, order assignment/publication pointers, event result link and state constraints. Constraint replacement extends lab states; it does not remove clinical rows. No non-lab domain schema change.
- Consistent verified original backup: ignored `.venv/backups/phase3b1/before.sqlite3`. New `.venv/phase3b2-preview.sqlite3` cloned from that backup and migrated explicitly using CAREFLOW_DB_PATH. Old clinical/auth/session rows and counts preserved; only additive migration/content-type/permission metadata allowed. SQLite integrity and foreign-key checks passed.
- Original `db.sqlite3`, backup, 3B-1 preview and historical documents have unchanged SHA-256 values. Source contains no committed databases, passwords or private test artifacts. C-drive backup untouched.

GitHub Actions runs execute system checks, migration consistency and the default regression suite. Chromium is local evidence, not part of the current hosted workflow. Application-level immutability/serialization tests do not certify database-level tamper resistance, external identity races, production concurrency or clinical correctness.
