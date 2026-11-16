# V3 architecture and security boundaries — v1.0

## Additive account module

The Django User model and all existing clinical models remain. The new accounts app introduces:

- Enrollment: one user, normalized case-insensitive unique email, patient/staff kind, requested/granted role, verification time, review status/reason/actor/time and optimistic version.
- EmailChallenge: one current challenge per enrollment/purpose, SHA-256 token digest, password-hash fingerprint, expiry and consumption time. Raw tokens are not stored in the database.
- AccountEvent: append-only through supported model/service APIs, enrollment, action, actor, reason, role and timestamp.
- RequestBucket: keyed HMAC of address/identity and fixed 15-minute bucket; counters use conditional updates and expire. Raw email/IP values are not persisted in rate keys.

One additive accounts migration creates these structures. No data migration rewrites User, Patient, SOAP, orders, results, payments or clinical audit rows.

## Patient flow

Registration → inactive account → email code → explicit confirmation with registration password → new fictional Patient and immutable PatientPortalAccount link → email login.

No caller-supplied patient ID, MRN, account flags or staff role can select existing ownership. Names are labeled fictional; DOB is a declared 2000-01-01 placeholder and sex Unknown. The account email is not copied into a clinical chart email field. Existing patient matching/invitations are deliberately not implemented.

## Staff flow

Application → inactive account → email code + registration password → verified/pending → Administrator approval or rejection.

Public choices are Physician, Nurse, FrontDesk, Lab Staff, Pharmacist, BillingStaff, RadiologyStaff and HospitalOperations. Public choices exclude Administrator and Django superuser/staff flags. Review requires the existing Administrator group and excludes patient-linked accounts. A conditional version/status update prevents stale or duplicate approvals; a reason is mandatory. Conflicting existing roles/portal links cause rollback.

The first hosting operator is provisioned through the trusted console command `bootstrap_demo_operator --email ... --confirm-synthetic`. It refuses to alter accounts if an Administrator already exists. This is an explicit hosting-owner bootstrap exception, not public self-registration or proof of mailbox delivery. It grants no Django superuser/is_staff flag.

## Authentication and recovery

The backend accepts verified, approved, active enrollment emails and preserves legacy usernames, including email-shaped usernames. It never interprets an unverified legacy User.email as an ownership claim.

Recovery applies to active verified enrollment accounts only. Codes expire after 20 minutes, are single-use, and are invalidated by password changes. Django password validators remain enabled and password changes invalidate existing sessions. Pending/rejected/inactive accounts do not receive recovery access. Existing unbound demo usernames require their known demo password or operator-assisted recovery.

Email bodies use the configured canonical origin, never the incoming Host header. Codes are submitted in POST forms, not URL paths/query strings. Activation requires the original registration password as well as the email code. Public responses avoid stating whether an email already exists.

## Security controls

CSRF remains mandatory. Account/login POSTs are limited per actual peer address (60/15 minutes) and normalized submitted identity (15/15 minutes). Arbitrary forwarded client addresses are not trusted. Behind a proxy this conservative address policy can rate-limit several users together; trusted edge controls must be assessed before wider use.

Sensitive responses are not cached, and same-origin referrers are retained so browser CSRF validation works. A no-referrer policy was rejected after real Chromium produced Origin:null and Django correctly denied the login. Null origins were NOT added to trusted origins.

Email delivery failures return a sanitized unavailable page; account creation is transactional. Audit events never include passwords, codes or email contents. Direct database administrators can bypass application-level history safeguards; no database-level immutability claim is made.

## Visual design and compatibility

V3 adds a blue theme over the retained v2 component system. Landing cards have real staff-application and patient-registration links. Existing status colors keep their semantic meaning. All previous role checks and workflow services remain; there is no automatic privilege expansion for an email registrant.

## Hosted demo boundary

Separate fail-closed settings require a strong secret, one HTTPS origin, persistent SQLite outside source, SMTP credentials and explicit hosted-demo enablement. Secure cookies, HTTPS redirect, HSTS, explicit hosts, WhiteNoise static assets and a WSGI server replace development defaults. Container startup checks migrations but never applies them automatically.

The SQLite deployment is limited to a small synthetic demonstration with one worker; it is not a multi-tenant production EHR. No real clinical data, billing, treatment recommendations or email addresses claiming existing patient ownership are permitted.
