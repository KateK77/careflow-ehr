# Unified staff and patient landing page

[Issue #48](https://github.com/KateK77/careflow-ehr/issues/48) · Branch `ui/unified-portal-landing` · Base `a9e0913b626b88908ad2ca3041d2ec9497ba7d15` (v1.0.0).

The previous standalone root template omitted a stylesheet link and linked only to staff sign-in. The updated root uses Django static tags for the shared CareFlow stylesheet and a small landing stylesheet. The staff and patient cards use the existing named sign-in routes. No authentication, role, database or migration changes are needed.

## Verification

Django system check passed and static-file discovery found both stylesheets. All 346 Django tests passed, including existing portal login, role and patient isolation checks. Four local Chromium workflows passed, covering the landing page, shared workspace UI, patient records and patient communication. The landing workflow verified successful CSS responses, keyboard activation of both login links and layout at 320, 390, 768 and 1440 pixels. Screenshots were inspected at 390 and 1440 pixels. All 48 pre-existing SQLite files retained their hashes. See the linked PR checks for GitHub CI.
