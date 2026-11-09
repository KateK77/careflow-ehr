# Historical documentation and language policy v1.0

Approved 2026-11-07. [Original approved request](request.md).

## Historical records

Preserve the original Phase 0 requirements, original ZIP and extracted package, and historical development/acceptance documents exactly as recorded, including Chinese text. Historical corrections belong in a dated addendum or a new version, with links to the original. Preserve Git history.

The archived requirements under `docs/requirements/v1.0/` and Phase 0 records under `docs/iterations/0001-foundation/` are immutable. The active root AGENTS rules may be extended to enforce this policy. Its [pre-policy snapshot](AGENTS.before.md) preserves the prior content. Append navigation links to existing documentation indexes without rewriting their historical content.

## Future development language

Write all new GitHub Issues, PRs, commit messages, requirements, architecture decisions, development reports, feedback summaries, test evidence and acceptance records in professional English. Accurately translate Chinese user feedback and instructions before documenting them on GitHub.

Preserve approved prompts verbatim in their original language. For a Chinese prompt, add a separate English translation alongside it. This verbatim-source exception also permits exact source filenames, paths, quotations and identifiers necessary for traceability.

## Versioning and authority

Keep source requirements as the source of truth. Use the [English requirements registry](../../../requirements/v1.0-en/README.md) for English reading copies. Each translation must state its source document, source version, translation revision and date, and link back to the immutable original. The registry supplies the forward link without editing archived files.

Product baseline v1.0 and English translation revision 1.0.0 are distinct versions. Future approved requirement changes create a new source version and corresponding English version. Translation corrections create a new translation revision and record the change. Do not silently introduce new requirements, resolve ambiguities, or change architecture through translation. Record uncertainty for clarification.

## Delivery records

Link each iteration to its Issue, branch, commit and PR. Preserve original prompts, provide English translations where needed, and record feedback, changed files, actual tests and remaining issues in English. Apply this policy within the current approved scope.
