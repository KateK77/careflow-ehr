# CareFlow EHR

CareFlow EHR is an independently developed educational and research prototype for electronic health records and hospital workflows. Its scope is inspired by workflows found in enterprise EHRs such as Epic. It uses original code and design.

**Use only synthetic data.** Keep real patient records, credentials, and production exports out of the application, repository, and logs. The scaffold is for local development and research.

## Run locally

Install Python 3.12 or newer and create a virtual environment from the repository root.

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on macOS or Linux. Then run:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open [the landing page](http://127.0.0.1:8000/). The [health endpoint](http://127.0.0.1:8000/health/) reports process availability.

```sh
python manage.py check
python manage.py test
```

See [architecture](docs/architecture.md) for module boundaries and the [roadmap](docs/roadmap.md) for planned work.
