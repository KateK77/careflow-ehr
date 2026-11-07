# 给 Codex 的开发指令：从零构建 CareFlow EHR

> 先阅读 `01_CareFlow_EHR_完整功能与界面规格.md`，下面是**第一轮给 Codex 的实际任务**。不要把完整实现一次性塞给 Codex；按阶段完成、测试、验收。

## 如何开始
1. 在 VS Code 中先打开你想存放该软件的**新空文件夹**（例如 `D:\AI-Workspace\Personal\careflow-ehr`），不要在现有 MedAgentBench、RAG 项目中直接创建本项目。
2. 把主规格 `01_CareFlow_EHR_完整功能与界面规格.md` 和 `AGENTS.md` 放进新目录（如将主规格放到 `docs/product-spec.md`）。
3. 打开 Codex 侧边栏，在这个项目目录里复制粘贴下面的第一轮 Prompt。
4. **第一轮只让 Codex 检查环境和做分阶段技术计划，不创建代码。** 审核它的回复后，第二轮才开始 Phase 0。

## Prompt 1：分析需求并制定开发计划（可以直接复制）

```text
You are my senior full-stack software engineer and technical lead. We are building an ORIGINAL, educational, demo-only healthcare EHR called CareFlow EHR, inspired by common EHR workflows, NOT an exact Epic software clone.

Read docs/product-spec.md and AGENTS.md completely, then inspect the current workspace and local environment before proposing any code changes.

Goals:
- A working multi-role EHR with synthetic patients: registration, scheduling, patient chart, ambulatory visit, notes, diagnosis, orders, laboratory results, inbox, and later nursing/inpatient/portal and AI-assisted chart review.
- Modern original UI: desktop clinical workspace with global header, navigation, patient context sidebar, task-oriented main area, contextual drawers, role-based dashboards, and a separate patient portal.
- All core actions must persist to a backend and database. NO fake buttons, no static-only prototypes marketed as functional.
- Demo/synthetic data only. Display a clear NOT FOR CLINICAL USE label. No real prescriptions, payments, PHI, real EHR integrations, or claims of compliance/certification.

Preferred stack: React/TypeScript/Next.js frontend; Python/FastAPI backend; PostgreSQL plus SQLAlchemy/Alembic; use a SQLite fallback only if local Docker isn't available. Tests with Pytest and Playwright when feasible. Propose changes if necessary and explain why.

IMPORTANT FOR THIS FIRST TURN:
1. Do NOT create, delete, or modify any files yet.
2. Inspect the existing folder, operating system, runtime versions, Docker/Git/Node/Python status, and available project files. Do not touch unrelated projects.
3. Summarize all major modules and identify gaps/ambiguities in the product spec.
4. Propose an incremental milestone plan, emphasizing an end-to-end functional vertical slice instead of generating every screen at once.
5. Show the exact Phase 0 file/folder structure and commands you intend to run.
6. Explain the risks, dependencies and acceptance tests.
7. STOP and ask me to approve the Phase 0 implementation plan before writing code.

Work in small, inspectable, testable steps. At every completed step report files changed, how to run, tests actually run, remaining issues, and the next proposed step. Never claim a test passed unless it was executed.
```

## Prompt 2：只有在你认可计划后才发送

```text
I approve the Phase 0 plan, with these constraints:
- Work only inside the currently opened CareFlow EHR project workspace.
- Create the monorepo, minimal running frontend/backend, migrations, synthetic seed data, simple demo login, role-based route protection, and an original app shell with the demo warning.
- Build and test one working path end to end: demo user signs in -> opens dashboard -> opens a real patient list from API -> opens a patient snapshot from database.
- Do not build appointments, notes, lab, pharmacy, patient portal, or AI yet.
- Do not delete files or modify unrelated projects. Use mock clinical data only.
- Add README with exact commands and .env.example. Run lint/typecheck/API tests where possible and report their real results.
- When done, STOP and wait for my review before Phase 1.
```

## 评估 Codex 的输出是否合格
- 它有没有先读取需求文档、确认当前文件夹/环境？
- 它有没有把巨大需求拆成可测试的阶段？
- 它有没有明确区分 Epic 公开的功能事实、我们的设计假设、未来功能？
- 它有没有创建真实 DB + API，而不是把所有患者写死在前端 JSON 里？
- 它有没有提供启动步骤、测试结果和截图或可访问的本地 URL？
- 它有没有在遇到 Docker 或版本问题时提出替代方案，而不是偷偷绕过安全/测试？
- 它有没有在首次任务结束后停下来等待你的审阅？

## 项目实施节奏
- Phase 0: 可运行基础框架、登录、患者列表。
- Phase 1: 预约、登记、签到与患者摘要。
- Phase 2: 生命体征、过敏、药物核对、诊断、SOAP 笔记、签署。
- Phase 3: 医嘱→实验室发布结果→Inbox 审阅；门诊闭环。
- Phase 4: 药师/护士 MAR/住院/急诊/影像。
- Phase 5: 门户、账单演示、人群分析、标准接口演示。
- Phase 6: 有引用的 AI Summary/Note Draft、质量和部署演示。

每个阶段都由你手动验收、Git commit，然后才能进入下一阶段。
