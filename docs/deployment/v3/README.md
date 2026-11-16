# V3 zero-budget hosted demo

Current scope: username/password/confirmation, with no email service. Budget: USD 0/month. Public runtime: [jiawen.pythonanywhere.com](https://jiawen.pythonanywhere.com/), verified on 2026-11-15. Never enable paid tiers, billing, domains or automatic top-ups.

## Source link versus running website

[GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) serves static content. Django sessions, database writes and workflows need an application server. A verified public HTTPS URL can later be added to the repository or profile. Keep source private unless the owner separately authorizes making it public; non-collaborators cannot access a private README.

## Selected free host — PythonAnywhere

PythonAnywhere documents a [free account](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [SQLite support](https://help.pythonanywhere.com/pages/KindsOfDatabases) and [existing Django deployment](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/). At review time the free tier has one web worker, 512 MiB storage and a one-month app expiry. Renewal, storage, CPU and network restrictions matter; this is not unlimited/permanent hosting.

The user selected this free-hosting route on 2026-11-15, created account Jiawen, authorized deployment securely and opened the required Bash console. The API token is locally Windows-DPAPI encrypted, never committed or printed. No sender account is needed. No paid plan was enabled. If a future requirement costs money, obtain separate approval.

## Configuration

Install requirements-hosted.txt and use careflow.settings_hosted_demo through WSGI. Configure outside Git:
- CAREFLOW_HOSTED_DEMO=1
- CAREFLOW_SECRET_KEY: new random secret with at least 50 characters
- CAREFLOW_PUBLIC_ORIGIN: actual public HTTPS origin with no path
- CAREFLOW_HOSTED_DB: absolute path on persistent storage outside the source tree
- CAREFLOW_TRUST_HTTPS_PROXY=1 only behind a proxy that strips spoofed headers

Do not publish SQLite files, local QA artifacts, environment files or passwords. Email uses Django's dummy backend; there are no registration email fields or mail routes.

## Provision only a NEW database

After confirming the configured file is absent and is a dedicated hosted-demo location:

```text
python manage.py migrate --settings=careflow.settings_hosted_demo
python manage.py bootstrap_demo_operator --username demo-operator --confirm-synthetic --settings=careflow.settings_hosted_demo
python manage.py collectstatic --noinput --settings=careflow.settings_hosted_demo
python manage.py check --deploy --fail-level WARNING --settings=careflow.settings_hosted_demo
```

The bootstrap command prompts twice for a hidden password and refuses to replace an existing Administrator. Do not upload or migrate any original or preview database. Public users choose their own passwords; do not publish shared demonstration credentials.

Docker uses non-root Gunicorn and WhiteNoise, with one worker/thread and persistent /data. Startup requires an existing initialized database, checks unapplied migrations and collects static files; it never seeds or migrates automatically. This portability artifact does not imply PythonAnywhere offers Docker hosting.

## Go-live gates

Verify actual HTTPS/CSRF/cookie/proxy behavior, static assets, persistent storage, backup/restore, administrator bootstrap, patient/staff isolation, signup abuse controls, rate limiting behind the real proxy, quotas and renewal. Verify no hidden costs. Only then publish the actual website URL.

Local container QA uses a disposable tmpfs database and simulated trusted HTTPS headers. It is not external TLS, public availability or production validation.

References: [Django deployment](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) · [Django authentication](https://docs.djangoproject.com/en/5.2/topics/auth/default/) · [WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html).

## Actual public deployment

See [deployment verification](../../iterations/0029-v3-email-access/public-deployment.md). Python 3.13 and Django 5.2.19 run through PythonAnywhere WSGI and a dedicated virtual environment. WhiteNoise serves collected static files. HTTPS is forced; DEBUG is false; secure cookies and CSRF remain enabled. Proxy-header trust was not enabled.

The host has a NEW database outside the source directory, a new secret key and eleven initially provisioned accounts with distinct passwords. A dedicated, one-time operator script created the initial synthetic accounts in an empty database; it did not run local preview seed commands against existing data. Two more synthetic accounts were created by the actual browser verification. No local patient data, preview databases or local credentials were uploaded.

A SQLite online backup and restore into separate new files passed integrity and account-count checks. Automated scheduled backups are not configured; the owner must arrange periodic private backups and free-app renewal. Keep the private environment, database, backup files and owner credentials out of static-file mappings and Git.

The current rate limiter uses REMOTE_ADDR and does not trust user-supplied forwarding headers. PythonAnywhere proxies may aggregate users under the same address, so shared-IP rate limits can affect multiple visitors. This was not load-tested or relaxed. The single worker and free-tier quotas constrain concurrency and availability.
