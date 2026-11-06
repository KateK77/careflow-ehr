# Architecture

CareFlow starts as a Django modular monolith. Server-rendered templates provide the browser interface, Django handles HTTP routing and the data layer, and SQLite keeps local setup lightweight. Plan to adopt PostgreSQL before testing shared clinical workflows that depend on concurrent writes.

## Boundaries

- `careflow/` holds application settings and root URL routing.
- `careflow/core/` owns the landing page and process health endpoint.
- Add each domain as a Django app when its first workflow is specified. Keep its models, migrations, views, and tests together. Use explicit service interfaces for workflows that span domains.
- Keep FHIR mapping and exchange in an interoperability module, with explicit profiles and conformance tests when exchange requirements are defined.

## Research data and access

Build identity, role-based access, and auditable data access before implementing workflows that expose synthetic patient charts. Keep synthetic fixtures reproducible and avoid importing production exports. Introduce environment-specific settings, secret management, and a deployment review before hosting any shared instance.
