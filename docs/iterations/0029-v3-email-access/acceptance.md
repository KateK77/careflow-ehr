# V3.1 acceptance and limits

Status: automated checks recorded in verification.md; user manual acceptance pending. No public deployment has occurred.

Implemented:
- Blue-led responsive home, staff/patient entry points and real registration links.
- Username + password + confirmation; no email field, code or mail dependency.
- Explicit synthetic consent, validation and new fictional patient chart.
- Staff application, pending access denial, administrator review and role activation.
- Audit events, transactional writes, CSRF and existing patient/role isolation.
- Hosted runtime package and fresh local preview launcher.

Manual review checklist:
1. Open the v3 homepage and confirm the blue interface and both registration links.
2. Register a patient with a unique lowercase username and matching strong passwords.
3. Confirm missing consent or mismatched passwords prevents registration.
4. Sign in to the Patient Portal; confirm the new fictional chart is separate.
5. Apply for a staff role and confirm login is unavailable before approval.
6. Sign in as the local Administrator, review the application with a reason, then sign in as the approved staff member.
7. Review desktop/mobile layouts and existing clinical workflows.

No new manual observations are claimed. Automated browser tests do not replace native paid CUA or user acceptance.

Limits:
- No email delivery/verification or email password recovery, by latest instruction.
- New charts have documented fictional demographic placeholders; no existing chart linking.
- Staff identity/employment is not independently verified.
- Local preview creates new isolated fixtures on each launch.
- No public URL, hosting account or TLS endpoint has been provisioned.
- Original clinical prototype limits, deferred features and historical manual evidence remain unchanged.
- No comprehensive accessibility, concurrency, penetration, provider-load or clinical certification claims.

## Owner selection of the final local version

The owner selected the current website as the final version for this round and requested GitHub publication, public access and an account/rules guide. See [final handover](final-handover.md). Earlier acceptance statements above are preserved as history. This selection does not claim unperformed security/clinical tests or a completed public deployment.
