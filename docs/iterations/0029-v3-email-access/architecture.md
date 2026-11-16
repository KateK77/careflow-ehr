# V3.1 architecture — username accounts

## Incremental integration

Retain Django 5.2, server-rendered templates, SQLite and the existing clinical modules. v3.css imports the retained v2.css and applies blue branding; status colors retain their meaning. New account routes appear in both portal entry flows. Existing staff/patient login classes, authentication backend and clinical role definitions are unchanged from the parent commit.

## Account lifecycle

Registration asks only for username, password and confirmation, plus explicit fictional-data consent. Staff applications additionally select a requested role. Usernames are 3–40 lowercase ASCII letters, digits, dots, underscores or hyphens. Login follows existing Django username semantics. Legacy usernames, including email-shaped usernames, remain supported; new signup does not use email.

Patient signup transactionally creates an active Django User, approved Enrollment, NEW synthetic Patient, immutable PatientPortalAccount association and audit events. The fictional placeholder name is Synthetic Visitor; DOB 2000-01-01 and unknown sex are explicitly fixture defaults, not inferred demographics. Users cannot claim existing charts using injected IDs or MRNs.

Staff signup creates an inactive User and pending Enrollment without a role or patient link. Administrator review requires a reason, expected version and permitted role. A conditional update serializes decisions; stale/replayed decisions fail, conflicting existing account permissions roll back. Public registration/approval cannot grant Administrator or Django superuser access. All eight existing non-administrator staff role names are retained.

Enrollment stores kind, status, requested/granted role, reviewer, review reason, timestamps and version. AccountEvent records registration and review actions; model-level edit/delete is rejected. This is not database-level audit immutability against privileged SQL. RequestBucket stores keyed HMAC identifiers and bounded fixed-window counts. The new accounts migration is additive; no prior clinical migration is edited. The discarded, unpublished email draft schema was replaced before commit and applied only to disposable draft QA databases; those old QA files are preserved and never migrated.

## Security and access

Use Django password hashing/validation, CSRF middleware and existing PortalBoundary. Patients cannot access staff URLs; staff cannot authenticate into the patient portal. Each signup gets a separate chart. Anonymous/public requests cannot approve staff. No mail delivery, mailbox claim, email token or self-service recovery exists.

POST requests to signup/login have 60 attempts per IP and 15 per submitted username per 15-minute fixed window. Client-supplied forwarding headers are ignored. Behind a shared proxy this may throttle legitimate users; production traffic policy remains unvalidated. Database contention fails with a sanitized response. Identity HMACs do not store raw usernames/IPs. Authentication pages use no-store and same-origin referrer policy; removing referrers entirely caused a tested Origin:null CSRF failure and was corrected without trusting null origins.

The first hosted operator can be created only through the trusted bootstrap command with an explicit synthetic flag and hidden password confirmation. Existing Administrators cannot be overwritten. This operator is in the Administrator group, not Django superuser/is_staff. The administrator must independently review applicants; signup does not prove employment or real-world identity.

## Hosting boundary

Hosted settings require a strong secret, explicit HTTPS origin/host, secure cookies, persistent SQLite outside the source tree, and WhiteNoise static handling. No SMTP settings are required. Docker runs as a non-root user with one worker/thread; startup checks migrations but never automatically migrates or seeds. Initial provisioning is explicit on a NEW database.

SQLite, one-process operation, account quotas, backup/restore, abuse monitoring, user support and public hostname validation limit this prototype. Budget is zero and no provider account exists yet. Public hosting is not complete; local testing is not production security or clinical validation.
