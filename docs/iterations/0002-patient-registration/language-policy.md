# Documentation language policy — review follow-up

Policy version 1.0, dated 2026-11-07. Related to [Issue #3](https://github.com/KateK77/careflow-ehr/issues/3) and [PR #4](https://github.com/KateK77/careflow-ehr/pull/4).

## Approved request and implementation

The [verbatim approved English request](../../policies/language/v1.0/request.md) establishes English as the mandatory language for new development records and requires immutable historical sources.

Added the English translation of the complete v1.0 specification, the original package guide and the original Codex guide. Added separate English versions of both approved Chinese iteration prompts, with source links and explicit versions. Preserved the original English prompt bodies inside the translated Codex guide. Added a source-hash manifest and a registry that links each source to its English reading copy.

Appended the policy to the active root AGENTS rules and navigation indexes. Preserved the prior root rules in a separate snapshot. Historical requirements, Phase 0 development reports, original approved prompts, ZIP and extracted originals retain their original bytes. Existing historical GitHub records retain their original language. New records follow English conventions.

## Validation

Source hashes, historical-file preservation, documentation links, S01–S27/W01–W12 coverage, section coverage, embedded prompt preservation and append-only changes are checked before delivery. These structural checks support review and do not substitute for a bilingual semantic review.

Application tests are outside this documentation-only follow-up. Application code and configuration are hash-checked for preservation. No database commands are run. The original requirements remain authoritative if a translation discrepancy is found.

## Maintenance

Future Chinese approved prompts retain their verbatim original and receive a separate English translation. Record Chinese feedback in accurate professional English on GitHub, retaining its source for traceability. Use a new translation revision for corrections, and an approved new source version for requirement changes.

## Completed checks

- SHA-256 verification preserved all 60 pre-existing files outside the three explicitly append-only active documents, including archived requirements, approved prompts, original ZIP and extracted files.
- The active root rules and two documentation indexes were extended without rewriting their prior content.
- Translation coverage matched 27 screens, 12 workflows, 11 main sections and 31 numbered subsections. All 40 entity signatures and 36 API declarations present in the source were preserved.
- All 61 relative documentation links checked successfully. The two original English guide prompts were preserved verbatim, and all six source-manifest entries matched their hashes.
- Git diff whitespace checks passed.
