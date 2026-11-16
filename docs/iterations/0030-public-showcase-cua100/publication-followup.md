# Showcase publication follow-up

## User feedback (original)

##  â€这是啥？

你把测试结果推送到之前那个页面展示成果那里

## English translation

What does the corrupted text mean? Publish the test results on the earlier project showcase page.

## Changes and verification

The catalog renderer contained the UTF-8 dash bytes decoded as Windows-1252 text and saved again. This is a publication encoding defect, not a test term or a changed result. Replace the corrupted display punctuation with ASCII separators and regenerate all 100 task headings. Use explicit UTF-8 file reads and writes.

The existing GitHub showcase README now presents the native results before the main screenshot: 85/100 passed, difficulty-level counts, read/write group rates, estimated cost, and direct links to task definitions, screenshots, CSV and failure analysis. The five difficulty rows are computed from the unchanged published results JSON.

All 23 benchmark unit tests passed. Catalog data remains identical to tasks.json, generated task Markdown matches the renderer, all 100 task headings are present, and current benchmark/showcase text was checked for the observed mojibake pattern. No application code, databases, native evidence, pass/fail results or historical source documents were modified. No paid API requests or repeat browser acceptance runs were made.

This follow-up remains on docs/public-showcase-cua100, Issue #62 and PR #63. Main and the public application's runtime remain unchanged. Final publication CI is tracked in the existing PR.
