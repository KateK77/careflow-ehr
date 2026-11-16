# V3 zero-budget hosted-demo preparation

Current scope: username/password/confirmation, with no email service. Budget: USD 0/month. No public runtime has been provisioned. Never enable paid tiers, billing, domains or automatic top-ups.

## Source link versus running website

[GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) serves static content. Django sessions, database writes and workflows need an application server. A verified public HTTPS URL can later be added to the repository or profile. Keep source private unless the owner separately authorizes making it public; non-collaborators cannot access a private README.

## Free candidate

PythonAnywhere documents a [free account](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [SQLite support](https://help.pythonanywhere.com/pages/KindsOfDatabases) and [existing Django deployment](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/). At review time the free tier has one web worker, 512 MiB storage and a one-month app expiry. Renewal, storage, CPU and network restrictions matter; this is not unlimited/permanent hosting.

The owner must first authenticate a free host account securely and authorize source access. Do not send passwords in chat. No sender account is needed. If a required feature costs money, stop. No host login or public domain is currently available to this task.

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
