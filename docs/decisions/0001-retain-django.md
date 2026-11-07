# ADR 0001 — Retain the Django foundation

Status: Accepted for the current foundation.

The supplied product package recommends a separate Next.js and FastAPI stack. The repository already contains a Django modular monolith, and the user directed development to build on it. Continue with Django, server-rendered templates, and SQLite for local development. Use Django apps and migrations as new domains arrive. Add internal JSON endpoints alongside the relevant domain when a workflow needs them.

Revisit PostgreSQL before validating concurrent shared clinical workflows. Hosting, external integrations, and framework changes require a separate decision. Issue #1 delivers documentation and workflow only.
