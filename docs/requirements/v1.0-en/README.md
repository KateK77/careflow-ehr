# English requirements baseline v1.0

English translation revision 1.0.0, dated 2026-11-07. Sources remain authoritative. [Language policy v1.0](../../policies/language/v1.0/README.md).

| Record | Source version | Immutable original | English version |
| --- | --- | --- | --- |
| Product specification | 1.0 | [Chinese specification](../v1.0/product-spec.md) | [English specification](product-spec.md) |
| Development-package instructions | 1.0 | [Chinese package README](../v1.0/README.md) | [English package README](package-readme.md) |
| Original Codex guide | 1.0 | [Mixed-language guide](../v1.0/codex-prompts.md) | [English guide](codex-prompts.md) |
| Original workspace rules | 1.0 | [Original English AGENTS](../v1.0/AGENTS.md) | Already English, use the linked original as the historical reading copy |
| Approved Phase 0 prompt | 1.0 | [Original Chinese prompt](../../iterations/0001-foundation/prompt.md) | [English prompt](../../iterations/0001-foundation/prompt.en.v1.0.md) |
| Approved Phase 1A prompt | 1.0 | [Original Chinese prompt](../../iterations/0002-patient-registration/prompt.md) | [English prompt](../../iterations/0002-patient-registration/prompt.en.v1.0.md) |

The [source manifest](source-manifest.json) records source paths, SHA-256 hashes and translation links. The source documents retain their original contents, including recommendations made before Django was selected. Read [ADR 0001](../../decisions/0001-retain-django.md), [ADR 0002](../../decisions/0002-patient-management-access.md) and approved iteration scope alongside the translated product baseline.

## Translation notes

- Source section 1 uses hyphenated examples such as `in-progress` and `no-show`, while section 3.5 uses `in_progress` and `no_show`. Both forms are retained. A future implementation decision must choose canonical state values.
- Source role names include Administrator/Admin and BillingStaff/Billing. The original distinctions remain visible.
- Source section 8 places the full W01 portal flow before the portal phase. Iteration plans must explicitly track when that complete acceptance scenario becomes available.
- The English version preserves the original future-state requirements. It does not certify that the current application implements them.
