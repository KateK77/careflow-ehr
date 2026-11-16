# Staff signup/login feedback — 2026-11-15

## User report (original)

> 我试了，其他账号我自己无法注册新账号，登录不进去，只有你注册好的我能登录进去

> 注册成功，但是无法登录，patient就可以自己注册然后登录

English translation: The user could log in with pre-created accounts but could not log in with newly registered staff accounts. The follow-up confirms registration succeeded and independently registered patient accounts can log in. The supplied staff-login screenshot shows the generic incorrect-credentials error. No password is reproduced here.

## Confirmed cause and scope

Read-only inspection of the running v3 SQLite database showed newly submitted staff applications in pending state, with Physician requested and is_active=False. HTTP logs show successful registration redirects followed by staff-login responses remaining on the login form. Existing Django authentication correctly denies inactive accounts.

The confirmed defect is the ambiguous error message for a pending staff applicant who supplies the correct password, not a failure to persist registration and not authorization to bypass staff review. New patient signup and login were confirmed by the user. Do not infer manual acceptance of additional boundary cases.

Two focused tests failed against the previous implementation: correct pending credentials did not receive approval guidance, and the completion page lacked the administrator's review path.

## Change

- StaffAuthenticationForm preserves Django authentication and only changes the invalid-login message for an inactive, pending staff enrollment after checking its submitted password.
- It does not authenticate inactive users, grant a role or establish a session. Wrong passwords, nonexistent users, rejected applications and unrelated inactive accounts retain generic errors.
- Other failures also perform an additional password hash so the added password check is not skipped solely because no pending enrollment exists. This is not a claim of comprehensive timing-attack verification.
- Patient Portal authentication is unchanged and does not disclose staff application status.
- Staff login/registration completion explain the approval requirement and Staff applications review path.
- Six new unit tests cover pending/wrong/unknown/rejected/inactive/portal cases, post-approval login and explanatory UI.
- The browser workflow now requires the explicit pending message before separate administrator approval and successful login with the original password.

Existing accounts are not approved, reset or otherwise changed by this fix. The operator may approve them through the existing UI. No account named administrator automatically obtains administrative access.

## Verification and preservation

Results are recorded below after execution. Test databases are isolated and contain only synthetic fixtures. No paid Computer Use API requests, migrations of existing databases or PR merges are authorized.

The initial manifest hashes all 62 SQLite files present at the start of this follow-up. The user continued using the active preview during diagnosis: subsequent read-only inspection showed additional staff and patient registrations, so that active file legitimately changed. The other 61 files remain unchanged. Never describe the live preview's hash as unchanged across concurrent user actions. Existing pending accounts and the user's new active patient account remain present.


## Actual verification results

- Before fix: both targeted regressions failed (2/2), reproducing the missing pending-approval message and review guidance.
- After fix: 44 account/deployment tests passed, including six added cases.
- Full Django suite: **536 passed**, 105.608 seconds.
- Complete Chromium suite: **32 passed**, 123.819 seconds.
- System check: no issues. Migration consistency: no changes detected.
- The staff browser flow verifies pending login denial and explicit guidance, then a separate Administrator's approval, then successful staff login with the original password and preserved role restrictions.
- [Sanitized pending-login screenshot](screenshots/staff-pending-login.png): synthetic username; password field empty before capture.
- No new paid/native CUA run. Previous 21 offline CUA results remain historical and were not rerun for this login-message change.
- The local 8015 server was restarted against the exact same preview database with runserver only. No migrate/seed/registration commands ran on it; its hash was unchanged across the restart. New guidance returned HTTP 200.
- Other prior preview servers, main, original source worktree and C-drive backup were not changed.

Issue #60 and PR #61 track this follow-up on the existing feature/v3-account-registration branch. The PR records the exact follow-up SHA and latest CI result. No automatic approval of the user's staff applications and no PR merge.
