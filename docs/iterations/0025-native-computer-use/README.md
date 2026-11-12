# Native Computer Use harness

[Issue #50](https://github.com/KateK77/careflow-ehr/issues/50) · Base [draft PR #51](https://github.com/KateK77/careflow-ehr/pull/51) at `16775f36bbf74fb971046c4bd45e7c471e1fd698` · [Harness and commands](../../../tools/cua/README.md)

The harness is isolated from Django application code and production dependencies. It uses a new QA database per run and implements the native ComputerDriver contract in Chromium. It keeps one browser context for the duration of the SDK loop. An explicit API flag is required for native mode. Screenshots can be saved locally on request, and only action types are printed.

## Actual verification

- Windows with Python 3.13, OpenAI SDK 3.31.0 and Playwright 1.61.0.
- The offline rehearsal passed against the real CareFlow landing page and staff login.
- Both offline tests passed. They cover native request serialization and screenshot feedback through an in-process transport, same-page browser state, input, navigation and action policies, cooperative cancellation, and the explicit approval gate.
- The first runs found a browser-cache path mismatch and an exact-label selector mismatch. The matching Chromium cache and form-label verification resolved both.
- Zero live OpenAI API requests. The native model-driven smoke and Issue #50 manual acceptance are pending.
