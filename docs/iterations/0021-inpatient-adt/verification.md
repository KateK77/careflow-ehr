# Phase 8A verification

Django system and migration consistency checks passed. All 339 Django regression tests and 21 Chromium workflows passed. The new browser workflow exercises admission, bed transfer, physician discharge planning, discharge and bed release. The new service coverage includes concurrent allocation, role and patient boundaries, replay, stale writes, audit rollback and preservation of signed SOAP.

The separate Phase 8A clone applied only the imaging migrations and hospital.0001. Integrity and foreign-key checks passed. Existing rows in 58 source tables and all 202 schema objects were preserved, apart from additive Django metadata. All 39 existing SQLite files and the unified preview retained their hashes. See the associated PR for push and PR CI evidence.

Consolidated manual UAT remains pending.
