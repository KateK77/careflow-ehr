# CareFlow EHR — Original project setup guide

English translation revision 1.0.0, dated 2026-11-07. Source package v1.0. [Original Chinese README](../v1.0/README.md) · [Translation registry](README.md).

This requirements package describes an original healthcare EHR for learning and demonstration. It does not represent completed software or an official Epic product.

## Historical quick start — Windows, VS Code and Codex

1. Choose a separate new project folder such as `D:\AI-Workspace\Personal\careflow-ehr`. Keep it separate from existing MedAgentBench and RAG projects.
2. Extract the package and place its AGENTS.md, README.md and docs folder at the new project root.
3. In VS Code, use File > Open Folder, then open the Codex sidebar.
4. Read docs/codex-prompts.md and submit Prompt 1 to Codex.
5. First request environment inspection and planning. Obtain approval before generating the system.
6. After reviewing the plan, submit Prompt 2 to implement functioning software incrementally.

These are translated historical setup instructions. The existing project's approved architecture and workspace decisions govern current work.

## Package contents

- docs/product-spec.md contains the complete specification, 27 screens, domain models, workflows, permissions, APIs and testing requirements.
- docs/codex-prompts.md contains two ready-to-use prompts and a phased development plan.
- AGENTS.md defines the technical and safety constraints for Codex in the workspace.

DEMO ONLY / NOT FOR CLINICAL USE. Use synthetic patients only. Actual care and patient private information are prohibited.
