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

## Patient Portal sign-in smoke

```powershell
tools/cua/.venv/Scripts/python.exe tools/cua/smoke.py --scenario patient --mode offline
```

The first paid patient scenario stops at the visible sign-in form. It sends no credentials and allows no form submission. After explicit approval for this scenario, run from the repository root with the API key already set securely in the process environment:

```powershell
tools/cua/.venv/Scripts/python.exe tools/cua/smoke.py --scenario patient --mode native --model gpt-5.4 --approve-api-call --evidence-dir .venv/uat-followup/cua-patient-native-01
```

The evidence directory must be new. The run allows at most three Responses requests, 1,024 output tokens per request and six requested computer actions. Retries are disabled. An HTTP quota error stops the run and is recorded as blocked. PNG evidence is saved for the initial screen, completed SDK action batches and final verification. The JSON report includes requested action types, status and per-run usage totals. Cost uses uncached input pricing for the GPT-5.4 estimate. At 10,000 input tokens and the full 3,072-output-token budget, token charges would be about $0.071. This is an illustrative estimate, not a dollar cap. Screenshots and replayed history affect input usage. Missing usage is flagged, and the estimate excludes any separate fees or account pricing adjustments. [GPT-5.4 rates](https://developers.openai.com/api/docs/models/gpt-5.4)

Further Issue #50 scenarios should be separately approved in this order: linked patient sign-in and isolation, Administrator scheduling and check-in, Nurse assessment, Physician encounter and SOAP, Lab Staff publication and Physician release, Pharmacist handoff, and patient result visibility. Preserve shared synthetic fixture state only for the connected journey. Each scenario needs a scoped browser policy, observable checkpoints and independent budgets before live execution.
