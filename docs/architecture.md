# Architecture

CareFlow starts as a Django modular monolith. Server-rendered templates provide the browser interface, Django handles HTTP routing and the data layer, and SQLite keeps local setup lightweight. Plan to adopt PostgreSQL before testing shared clinical workflows that depend on concurrent writes.

## Boundaries

- `careflow/` holds application settings and root URL routing.
- `careflow/core/` owns the landing page and process health endpoint.
- Add each domain as a Django app when its first workflow is specified. Keep its models, migrations, views, and tests together. Use explicit service interfaces for workflows that span domains.
- Keep FHIR mapping and exchange in an interoperability module, with explicit profiles and conformance tests when exchange requirements are defined.

## Research data and access

Build identity, role-based access, and auditable data access before implementing workflows that expose synthetic patient charts. Keep synthetic fixtures reproducible and avoid importing production exports. Introduce environment-specific settings, secret management, and a deployment review before hosting any shared instance.

## Phase 1A patient increment

The `patients` app owns Patient, AuditEvent, demographic validation, backend staff-role policies, registration views and synthetic initialization. The shared UI and authentication views remain in `core`. The [patient-management decision](decisions/0002-patient-management-access.md) records access scope and transactional auditing. Django auth, sessions, messages and static files are enabled incrementally.

## Phase 1B scheduling increment

The scheduling app owns appointments, provider serialization rows and appointment events linked to existing AuditEvent records. Write services provide reservation conflict checks, state transitions and transactional audit writes. Scoped views reuse the existing staff-role policies. See [ADR 0003](decisions/0003-scheduling-and-checkin.md).

## Phase 2A clinical increment

The clinical app adds encounters, structured SOAP notes and clinical events linked to existing audits. Scoped clinical access is separate from demographic/scheduling access. Shared provider locks serialize clinical start/completion/signing with scheduling transitions. See [ADR 0004](decisions/0004-encounters-and-soap.md) and the [iteration record](iterations/0004-physician-workspace/README.md).
