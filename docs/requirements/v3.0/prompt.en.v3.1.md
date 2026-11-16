# CareFlow EHR v3 — implementation prompt, revision 3.1

Source: [original Chinese request](../../iterations/0029-v3-email-access/prompt.original.zh.md) and [latest feedback with translation](../../iterations/0029-v3-email-access/feedback.md).
This revision supersedes the email-registration part of v3.0. Historical prompts remain unchanged.

Build a blue-led v3 interface on the existing Django/server-rendered application. Retain appropriate semantic status colors, existing clinical workflows, staff/patient isolation, synthetic-only notices and real portal routes. Do not rebuild or discard the existing clinical platform.

Provide both patient registration and staff applications using Username, Password and Confirm password. Do not request an email address, send messages, require verification codes or claim mailbox ownership. Enforce the existing password policy, hash passwords with Django, validate duplicate usernames, retain CSRF protection and require explicit synthetic-data confirmation.

New patients receive a new fictional chart only, never an existing chart selected by name, MRN or request parameters. New staff have no active login or clinical role until an Administrator reviews the application with a reason. Public applications cannot create Administrators or superusers. Preserve existing username authentication and role definitions.

Use additive account models, transactional signup, optimistic review versions, account audit events, bounded auth request rates and safe error responses. Do not modify or migrate any original/preview SQLite database. Run regression and Chromium checks on isolated databases and report actual results.

Keep original requirements and English/Chinese historical documents. Record scope, source prompt, feedback, architecture, files, tests, limitations, Issue/Commit/PR links in English.

Budget is zero; there is no hosting account. Prepare deployable HTTPS/static/persistent-storage configuration with no email dependency. A GitHub source link alone cannot run Django. Do not enable charges, change repository privacy or fabricate a public deployment URL. Publish the implementation branch and stacked PR; do not merge or release. A real public runtime account and secure authorization remain necessary before external users can reach the site.

Preserve existing databases, signed notes, audit histories, all parent development branches and existing preview servers. No live paid Computer Use requests.
