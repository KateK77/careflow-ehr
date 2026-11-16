# CareFlow EHR v3 — visitor and operator guide

**DEMO — NOT FOR CLINICAL USE. Use fictional patient information only.**

This is the blue-interface v3 preview selected by the owner for this development round. The current implementation is reviewed through [PR #61](https://github.com/KateK77/careflow-ehr/pull/61), stacked on PR #59. The public synthetic demo is now online. The PRs remain open and unmerged.

## Open the application

- Current owner's local site: http://127.0.0.1:8015/.
- **Public website: [https://jiawen.pythonanywhere.com/](https://jiawen.pythonanywhere.com/).** Share this link with visitors. It does not require the owner's computer to remain on.
- The owner has now made the GitHub source repository public. See the [latest showcase](https://github.com/KateK77/careflow-ehr/tree/docs/public-showcase-cua100); main remains the default branch.
- GitHub Pages alone cannot run Django. The public runtime is PythonAnywhere; the public GitHub repository contains source and documentation, not a Django runtime.

## Register a patient account

1. Choose **Create patient account** on the homepage or Patient Portal login page.
2. Enter a unique username, password and Confirm password.
3. Explicitly confirm that only fictional patient information will be used.
4. Submit, then choose **Patient sign in** and use the credentials you just selected.

Usernames use 3–40 lowercase letters, digits, dots, hyphens or underscores. Passwords must be at least 12 characters and must not be common or entirely numeric. No email address, email confirmation or code is required. Email password recovery is not available.

Registration creates a separate fictional chart with documented placeholder demographics. It does not link to someone else's existing record. A newly created chart may be empty until the relevant synthetic workflow is performed. Patient accounts cannot access staff pages.

## Apply for staff access

1. Choose **Apply for staff access**.
2. Enter a unique username, password and Confirm password.
3. Select the requested staff role and confirm synthetic-only use.
4. Submit the application.
5. **Wait for an Administrator to approve it.** Successful registration does not activate a staff login.

The username does not determine permissions. Calling an account administrator or doctor does not grant that role. Public registration cannot grant Administrator or Django superuser access.

A pending applicant entering the correct password receives an approval-pending message. A wrong password or unknown username retains a generic login error. After approval, use the SAME registration password through **Staff Sign In**, not the Patient Portal.

## Administrator approval

The pre-created administrator on each environment is administrator.demo. Approval belongs to the **Administrator role**, not exclusively to this username.

1. Sign in through Staff Sign In.
2. Open **Staff applications** in the navigation.
3. Find the applicant and choose **Review application**.
4. Select **Approve** or **Reject**.
5. For approval, select the permitted role to grant.
6. Enter a review reason and choose **Save review decision**.

A pending account cannot approve itself. The server checks the Administrator role and the expected application version. If the application changed, reload before deciding; do not keep resubmitting a stale form. The reviewer, reason, time and decision are recorded. Rejected accounts remain inactive.

Creating additional Administrators is not part of public signup or this application-review form. It requires a separate trusted operator action.

## Demonstration accounts

The following usernames exist in both the owner's local preview and the public demo. They are separate accounts in separate databases. The public host uses a unique password for every account, supplied privately to the owner; local passwords will not work there. The pre-created accounts are already enabled.

| Username | Role | Portal |
|---|---|---|
| administrator.demo | Administrator — manages staff applications | Staff |
| frontdesk.demo | FrontDesk — registration and scheduling | Staff |
| physician.demo | Physician — authorized clinical workflows | Staff |
| nurse.demo | Nurse — authorized nursing workflows | Staff |
| lab.demo | Lab Staff — authorized laboratory workflow | Staff |
| pharmacist.demo | Pharmacist — authorized pharmacy workflow | Staff |
| billing.demo | BillingStaff — synthetic billing workflow | Staff |
| radiology.demo | RadiologyStaff — authorized imaging workflow | Staff |
| hospital.demo | HospitalOperations — hospital operations | Staff |
| patient1.demo | Patient — first linked synthetic chart | Patient |
| patient2.demo | Patient — different linked synthetic chart | Patient |

**Passwords:** supplied to the owner in a private local handover, not committed to Git or displayed on a public page. The current local seed uses a shared password, including the Administrator; publishing even a patient demo password would disclose that Administrator password. Do not publish these credentials. Visitors should create their own patient account or apply for staff access. The public deployment already uses separate credentials and its own synthetic database. Its owner credentials are also private. Do not publish Administrator credentials; visitors should register individually.

## Access rules and data

- Patients see only their own authorized portal data. Staff and patient login routes are separate.
- Staff privileges follow granted roles and existing patient/encounter ownership rules; a role does not confer unrestricted access to every module.
- No real patient information, real prescriptions, actual dispensing, real payments or clinical decisions.
- Existing signed documentation and workflow audit records remain subject to their original restrictions.
- Do not alter URLs or resubmit stale requests to bypass a denied action.
- Keep personal passwords private. Sign out before switching roles in the same browser.
- Use independent browser profiles or private windows when testing multiple users concurrently.

## Troubleshooting

| Symptom | Explanation / next step |
|---|---|
| Registered staff cannot log in | Ask the operator to review Staff applications; registration alone is insufficient. |
| Patient works but staff does not | Patients activate immediately; staff require review. |
| A new account fails with the published local demo password | New accounts use the password chosen at signup, not the seed password. |
| Wrong portal | Patient accounts use Patient Portal; approved staff use Staff Sign In. |
| Username unavailable | Choose another username; duplicate signup does not reset an existing account. |
| Too many attempts | The rate limit returns HTTP 429; wait for the stated retry interval. |
| Nothing in a new chart | New signup creates a new fictional record; existing patients are not automatically linked. |
| Friend cannot open 127.0.0.1:8015 | That is local-only; share https://jiawen.pythonanywhere.com/ instead. |
| Friend wants the latest showcase | Share the showcase branch link above; main stays the default branch. |

## Verification and publication limits

Latest application verification before this documentation handover: **536 Django tests and 32 local Chromium workflows passed**, plus [GitHub CI](https://github.com/KateK77/careflow-ehr/actions/runs/43797706595). The user confirmed patient registration/login and reported the staff pending-approval confusion, which was corrected. These observations are not comprehensive manual acceptance of every security or clinical boundary.

See [iteration evidence](../../iterations/0029-v3-email-access/verification.md), [staff-login follow-up](../../iterations/0029-v3-email-access/login-followup.md), and [zero-budget hosting preparation](../../deployment/v3/README.md). [Public deployment evidence](../../iterations/0029-v3-email-access/public-deployment.md) records nine successful browser checks on the actual HTTPS host. This is a synthetic demonstration, not production validation. Free hosting has capacity limits and requires periodic renewal; no availability guarantee is implied.
