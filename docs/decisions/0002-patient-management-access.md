# ADR 0002 — Patient management access and persistence

Status: Implemented for Phase 1A, pending user acceptance.

Continue the existing Django modular monolith and SQLite database. The patients app owns Patient and AuditEvent and supplies server-rendered pages. This is a single synthetic clinic. Administrator and FrontDesk may create and edit demographics. Physician and Nurse may read demographics. Other authenticated users are denied, as are direct write requests from read-only staff. Multi-role users receive the union of those four roles. There is no patient self-service account or clinical chart access in this phase.

A database unique constraint rejects case-insensitive MRN collisions. The form normalizes MRNs and warns about matching names and dates of birth, requiring explicit duplicate confirmation. An integer version provides optimistic update protection. Patient creation or update and its audit event share a transaction. Audit events contain actor, action, patient, time and field names, without copying demographic values or passwords.

Demo seeding is explicitly enabled in DEBUG with environment variables. It creates 30 deterministic patients and four staff accounts. Reruns preserve existing records and passwords. Passwords go through Django validation and hashing. Demo users have ordinary staff roles, without superuser or Django admin access.

Appointment, clinical records, detailed patient-assignment rules, audit administration, deployment hardening and PostgreSQL remain future decisions.
