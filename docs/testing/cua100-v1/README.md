# CUA-100 v1.0 — method and evidence

Tracking: [Issue #62](https://github.com/KateK77/careflow-ehr/issues/62).
[All 100 tasks](tasks.md) · [JSON contracts](tasks.json) · [Executable definitions](../../../tools/cua/benchmark_catalog.py)

## What is measured

A task passes only when the native model performs actual screenshot-driven computer actions and independent UI/database assertions pass. A generated answer alone is insufficient. Read-only tasks must preserve all business rows and all prior audit events; newly appended view/denial audits are allowed. Every task preserves a separate signed SOAP record and checks SQLite integrity and foreign keys.

Tasks 1–70 cover portal entry, scoped records/worklists and role/patient boundaries. Tasks 71–90 exercise field validation, writes, approval and clinical records. Tasks 91–100 add pharmacy, laboratory and multistep journeys. This is a deliberately scoped benchmark, not exhaustive coverage of every implemented module.

Non-login tasks use a role-specific session established through the real login form before the model starts. No force-login, authorization bypass or supplied session cookie is used. Direct URL probes begin at a clearly labelled test-only launcher with a single allowed link; the model must click it to exercise the real Django route. This does not claim that a normally hidden link is exposed in application navigation.

## Isolation and safety

Each task migrates a NEW temporary SQLite file, seeds only synthetic fixtures and starts a loopback WSGI server. Existing local/preview/public databases are never used. The server and browser are closed after the task. An independent local database hash manifest tracks preservation outside the task.

The existing native ComputerToolset driver supplies screenshots and real browser actions. The benchmark restricts origins, exact routes, POST destinations, actions and runtime; downloads, WebSockets, pop-ups and external navigation remain blocked. Pending native safety checks are refused. Credentials use local placeholders and masked screenshots; the model never receives the generated password. Page content is untrusted.

## Limits and cost

GPT-5.4 remains the previously verified computer-capable model. Each task permits 4, 10 or 14 API requests according to difficulty, with 1,024 output tokens per request, 16–85 computer actions and 120–360 seconds of cooperative runtime. HTTP retries are disabled. Requests stop on missing usage, quota errors or per-task estimated token cost reaching USD 0.80. The batch starts no new task when the USD 20 estimated ledger lacks a USD 0.80 reserve. An in-flight request can exceed an estimate; this is not an invoice-level hard cap. No automatic recharge.

The estimate uses uncached input at USD 2.50/million and output at USD 15/million. It is conservative for cached tokens and excludes account adjustments or separate fees. [Official model rates](https://developers.openai.com/api/docs/models/gpt-5.4).
[Official native ComputerToolset guide](https://developers.openai.com/api/docs/guides/tools-computer-use).

## Run

Use the existing CUA environment (OpenAI SDK 3.31.0, Playwright 1.61.0), its installed Chromium and a Django Python environment. From the repository root:

```powershell
$env:CAREFLOW_DJANGO_PYTHON = 'D:\AI-Workspace\Personal\careflow-ehr\.venv\Scripts\python.exe'
tools/cua/.venv/Scripts/python.exe -m unittest discover -s tools/cua -p 'test*.py' -v
tools/cua/.venv/Scripts/python.exe tools/cua/benchmark.py --mode offline --output .venv/cua100-offline --django-python $env:CAREFLOW_DJANGO_PYTHON
```

Paid execution requires prior owner authorization and a securely supplied process-only OPENAI_API_KEY:

```powershell
tools/cua/.venv/Scripts/python.exe tools/cua/benchmark.py --mode native --approve-api-call --model gpt-5.4 --ids CF-001,CF-006,CF-036 --output .venv/cua100-native --django-python $env:CAREFLOW_DJANGO_PYTHON --max-total-usd 20
```

Never put the key in a command, screenshot, report or repository. Local Windows authorization stores the supplied key only in an ignored DPAPI-encrypted file.

## Reporting

- **PASS:** all predefined observations/assertions pass.
- **FAIL:** a task ran but did not meet its contract, including model task failure or harness failure. Diagnose separately.
- **BLOCKED:** configuration, authentication/API/quota/infrastructure prevents execution.
- **NOT_RUN:** no attempt was made.
- Attempted pass rate = PASS / (PASS + FAIL).
- Overall pass fraction = PASS / 100.
- Execution coverage = (PASS + FAIL) / 100.

Blocked/not-run tasks remain visible; they are never quietly removed to inflate success. First native attempts are immutable. Any later retries must be reported separately. Prior nine live CUA passes from earlier branches are historical evidence, not results for these 100 new tasks. Offline Chromium rehearsals do not contribute to native pass rates.

## Current execution status

Native execution is complete: **85/100 passed, 15 failed**. Read/authorization: **69/70**; validation/write/clinical: **16/30**. There were no paid failure retries. Three initial zero-request startup blocks were fixed offline before their first paid attempts.

Read the [full results and 100 evidence links](results.md), [failure analysis](findings.md), [CSV](results.csv), [JSON](results.json) and [evidence integrity manifest](evidence-sha256.json). Total estimated token cost: **USD 3.379979**, from 336 responses. Offline verification: **536 Django tests, 44 CUA framework tests and 100 task rehearsals passed**. These counts remain separate from native results.

Evidence hashes refer to the **published Git blob bytes**, including LF-normalized JSON, rather than Windows working-copy CRLF bytes. Verify a text artifact using its raw GitHub download or git show HEAD:path. Binary screenshot bytes are unchanged.
