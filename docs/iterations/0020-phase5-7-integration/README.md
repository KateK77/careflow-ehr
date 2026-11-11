# Phase 5–7 integration baseline

[Approved development brief](prompt.md)

The integration branch starts at Phase 6B `14220599b2d4c10668b42853d59e071212a33be7` and merges Phase 7B `9170ba388f38c59f13f98190eb3f48ff3477e2a5` with both parents. The base branches and PRs #32, #34, #36, #38, #40 and #42 remain independent of this temporary branch.

Four files required manual resolution. Django settings retain all three apps, portal middleware, and both staff context processors. Root URLs retain portal, billing and imaging routes. Sign-in retains portal-account rejection and both specialist landing routes. Shared navigation shows both specialist workspaces and preserves clinical and patient navigation. Existing clinical templates, service code, CSS and migrations merged without manual changes.

The isolated `.venv/phase8-unified-preview.sqlite3` is a consistent SQLite copy of the verified Phase 6B preview. Only `imaging.0001` and `imaging.0002` were applied. No Phase 7 preview records were imported. Integrity and foreign-key checks passed. All source rows in 58 tables and 202 schema objects were preserved, apart from additive Django metadata. All 39 earlier SQLite files retained their SHA-256 hashes. Tests use isolated test databases.

Django system and migration consistency checks passed. All 335 Django regression tests and all 20 Chromium workflows passed. The branch is the temporary base for the Phase 8 PRs and has its own GitHub Actions push run. Manual UAT remains pending.
