# CareFlow EHR — 从零构建说明

这是一个用于学习与展示的原创医疗 EHR 软件项目的**需求包**，不是已完成的软件，也不是 Epic 官方产品。

## 快速开始（Windows + VS Code + Codex）

1. 选择独立的新项目文件夹，比如 `D:\AI-Workspace\Personal\careflow-ehr`；不要把文件放进现有 MedAgentBench 或 RAG 项目。
2. 解压此包，把这里的 `AGENTS.md`、`README.md` 与 `docs` 文件夹放进新项目目录的根目录。
3. 在 VS Code 中选择 **File > Open Folder** 打开这个目录，然后打开 Codex 侧边栏。
4. 阅读 `docs/codex-prompts.md`，将 **Prompt 1** 复制到 Codex。
5. 第一次只让 Codex 检查环境并制定计划；没有得到你的确认前，不要让它自动生成全部系统。
6. 阅读并认可计划后，再发送 **Prompt 2**，逐步实现可运行的真实功能。

## 文件说明
- `docs/product-spec.md`：完整功能规格、27 个页面、领域模型、工作流、权限、API 和测试要求。
- `docs/codex-prompts.md`：两条可以直接复制的开发指令，开发阶段计划。
- `AGENTS.md`：Codex 在此工作区持续遵守的技术与安全约束。

**DEMO ONLY / NOT FOR CLINICAL USE**。只允许合成患者数据，不允许真实诊疗或患者隐私数据。
