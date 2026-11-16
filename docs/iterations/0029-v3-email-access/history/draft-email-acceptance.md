# V3 acceptance and feedback — v1.0

User feedback: restore blue rather than making the site uniformly green; add email-bound registration for both patients and staff; make the eventual site accessible from a GitHub link. The user has no hosting platform and requires zero monthly cost.

## Implemented for review

- Blue primary visual system, separate staff and patient registration links, visible Email fields.
- Verification, resend, email login, recovery and explicit synthetic confirmation.
- New patient isolation and Administrator-reviewed staff roles.
- Preserved username accounts and existing clinical workflow access.
- Additive migration, isolated preview with clearly labeled local mail, and fail-closed hosted configuration.

## Actual evidence boundary

Developer-run Django tests, Chromium workflows and offline CUA rehearsals are automated observations. No new manual UAT, paid native CUA result, external inbox delivery or public deployment acceptance is claimed. Screenshots exclude credentials and verification/reset codes.

## Manual checklist

1. Check the blue landing on desktop/mobile and both registration links.
2. Register a fictional patient using a test email. Verify code + registration password. Sign in via Patient Portal and confirm a new separate chart.
3. Request recovery; set a new password with its code; verify the old password/session no longer works.
4. Apply as staff and verify email; confirm login remains denied before approval.
5. Sign in as Administrator, review Staff applications, choose an appropriate role and reason, then sign in as the approved applicant.
6. Check that privileged roles cannot be self-selected and denied chart routes reveal no protected data.
7. Confirm all local-preview mail comes from the private test outbox, not a real inbox.
8. After an external environment is authorized, repeat signup/recovery with actual email delivery and HTTPS. This remains outstanding.

## Deferred / blocked

External hosting account, delivery-capable sender and actual public URL are not available. Free hosting limits and periodic renewal are not guaranteed permanent availability. Existing-chart invitation/identity proofing, email-address change, MFA, account deletion/retention management, advanced abuse protection and production/multi-tenant isolation remain future work. Legacy demo email addresses are fictional and do not imply verified ownership.

No repository visibility changes, merges, paid plans, releases, production clinical use or public deployment were performed.
