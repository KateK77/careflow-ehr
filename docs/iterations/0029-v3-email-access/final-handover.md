# Final local version and publication request

Date: 2026-11-15, America/Chicago.

## Original user instruction

> 好的，这个现在就是最终版本，你能把它搞在我的github上，别人能点开网站，然后你把你注册的账号，密码也写出来，并且那些规则就是工作人员账号都要通过审批什么的也搞出来

English translation:

> Okay, this is now the final version. Can you put it on my GitHub so other people can open the website, and write down the accounts and passwords you created, along with rules such as all staff account applications requiring approval before login?

## Interpretation and completed preparation

The user selected the current local website as final for this round and requested publication and a usage guide. This does not fabricate comprehensive UAT of untested cases or silently merge the accumulated branch stack.

[Visitor/operator guide](../../user-guide/v3/README.md) documents both registration flows, usernames, password handling, role approvals, portal isolation and common errors. The owner's actual current local demonstration credentials are recorded in an owner-only local handover, not in the Git repository. Because the current seed password is also the Administrator password, publishing it with a patient username would disclose privileged access.

Source already exists on feature/v3-account-registration in PR #61, stacked on PR #59. This documentation follow-up uses the same issue/branch/PR. No application, database, password or account approval is changed by the guide.

## Public access dependency

Budget remains zero and no hosting account was available at the start of this request. A source repository is not a Django runtime; the repository remains private.

Two options were presented: a free PythonAnywhere runtime requiring owner signup/authorization, or a temporary Cloudflare Quick Tunnel requiring the local computer to stay online. A temporary tunnel is not permanent hosting and must not be labeled as such. No existing local clinical database is to be exposed or copied to a public runtime.

The Sites plugin was inspected: its hosted server format is a Cloudflare Worker ES module, not this Django/SQLite runtime. No replacement mock site was created.

A real site URL is pending the hosting choice and actual deployment verification. No placeholder URL is presented as live. No charges, repository visibility change, automatic merge or release tag.

## Hosting selection

The user selected free PythonAnywhere hosting, so the website should operate independently of the local computer. Temporary tunnels were not selected. Account registration and secure authorization remain required before deployment; no hosting account, paid plan or public site was created by this documentation step.

## Documentation verification

Local Markdown targets resolve; Django system checks pass; migration consistency reports no changes; Git whitespace checks pass. This follow-up changes documentation only and does not repeat local clinical/browser testing. Latest application evidence remains 536 passing Django tests and 32 Chromium workflows. GitHub CI runs separately on the new documentation head. No SQLite writes, password resets, approvals, application changes or main-branch merge were performed.
