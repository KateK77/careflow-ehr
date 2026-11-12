# CareFlow native Computer Use smoke harness

Uses the official OpenAI Python SDK's `ComputerToolset` and the Responses API native `computer` tool. The browser driver supplies screenshots and applies coordinate-based actions. The SDK continues the Responses conversation with a fresh screenshot after each tool call. Playwright supplies the browser controls. [Official OpenAI documentation](https://developers.openai.com/api/docs/guides/tools-computer-use)

## Windows setup and no-cost verification

Use Python 3.13 and the prepared `tools/cua/.venv` for OpenAI SDK and Playwright. The project `.venv` supplies Django. Run from the repository root.

```powershell
tools/cua/.venv/Scripts/python.exe -m pip install -r tools/cua/requirements.txt
# Run only if the matching Chromium build is missing from your Playwright cache.
tools/cua/.venv/Scripts/python.exe -m playwright install chromium
tools/cua/.venv/Scripts/python.exe tools/cua/smoke.py --mode offline
tools/cua/.venv/Scripts/python.exe tools/cua/test_smoke.py -v
```

If the runtime changes the default browser cache, set `PLAYWRIGHT_BROWSERS_PATH` to the existing cache containing the Chromium build installed by Playwright 1.61.0. Use `--django-python` if the Django virtual environment is elsewhere. Optionally pass `--evidence-dir` with a new directory outside Git to save the two PNG screenshots.

The offline rehearsal executes a fixed SDK action against the real Django landing page. The tests use an in-process mock transport to exercise the SDK's native request and screenshot continuation. Neither path contacts OpenAI.

## API-backed smoke, pending explicit approval

Use only after approval for paid requests. Supply `OPENAI_API_KEY` through the process environment without putting its value on a command line, in an evidence directory, or in Git. Choose a model available to your project that supports the native computer tool.

```powershell
tools/cua/.venv/Scripts/python.exe tools/cua/smoke.py --mode native --model <computer-capable-model> --approve-api-call
```

The model receives the landing screenshot and chooses the click. The harness verifies the resulting URL, staff sign-in heading and credential controls directly. Each run creates a freshly migrated, empty SQLite database in a temporary directory and serves Django on an ephemeral loopback port. The browser is private and ephemeral. The smoke permits GET/HEAD only to the three public entry pages and local static files. It blocks other origins, form submissions, WebSockets, pop-ups and downloads. Pending safety checks fail closed. The run has a 16-action callback budget, five Responses steps, a 15-second HTTP timeout without retries, browser timeouts and a cooperative session deadline. Ctrl+C triggers cleanup. An in-flight synchronous request can take until its HTTP timeout to return.

## Diagnose a failed native smoke

The failure line reports the stage, exception class, latest HTTP status, recognized API code, compatibility hint and request counts. An HTTP response confirms delivery of the latest request. An attempt without a response does not establish delivery. Unrecognized API codes are redacted. The harness never prints the raw exception, response or screenshot data.

- `responses_validation` with `max_output_tokens` means the model response ended at the output budget. Review the task and explicitly approve any larger budget before retrying.
- `computer_approval` with `safety_check_refused` means the SDK received a pending safety check. Inspect the scenario and keep the refusal in place unless a separate review authorizes a narrowly scoped policy change.
- `responses_api` with a model or tool hint means the API rejected configuration. Check project access and native `computer` support for the selected model.
- `step_limit` or `action_refused` means a local run boundary stopped execution. Review the scenario before changing a limit.

The prior generic `ComputerUseError` line cannot identify the original stage. SDK 3.31.0 can emit it for incomplete responses, replay/schema errors, safety refusal, exhausted steps, invalid screenshot output or cancellation. HTTP model/tool rejection normally raises an SDK API exception instead. Offline tests reproduced incomplete output and safety refusal without live requests.

## Issue #50 follow-on

After the live smoke passes, extend the policy and fixtures for scoped synthetic role sessions and writes. Follow the [Issue #50 scenario checklist](../../docs/iterations/0024-workflow-verification/computer-use.md) for the patient login, role denials and clinical handoffs. Review each writable workflow's allowed routes and evidence handling before enabling it. This smoke does not sign in or execute those scenarios.
