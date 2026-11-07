# Approved Phase 0 prompt

CareFlow EHR 的 D 盘迁移验收通过。

现在正式批准开始 Phase 0：项目文档体系与 GitHub 开发工作流建设。

正式项目目录：\
D:\AI-Workspace\Personal\careflow-ehr

GitHub：\
KateK77/careflow-ehr

请在现有 Django 项目基础上执行以下任务。

## 1. 建立 GitHub 迭代管理

- 从 main 创建开发分支 phase/0001-foundation。
- 创建 Phase 0 GitHub Issue，记录需求、范围和验收标准。
- 保留现有 Git 历史，不重新初始化项目。

## 2. 建立完整的开发留痕体系

在 docs/ 中建立合理的文档目录，包含：

- 产品需求与规格版本
- 每轮开发 Prompt 原文
- 用户反馈与变更请求
- 软件架构与技术决策
- 每轮开发报告
- 测试与验收结果

每一轮的记录都必须能对应 GitHub Issue、Commit 和 PR。

## 3. 整理 Epic-inspired EHR 产品规格

阅读 D 盘现有的产品需求文档。

将它们整理为后续开发的正式需求基线，纳入 Git 版本管理。

注意：

- 保留原始 ZIP 和解压文档。
- 不覆盖现有根目录 README.md 和 AGENTS.md。
- 如果规格文件与现有项目文件同名，应采用合理的独立目录。
- 不要将本地数据库、缓存、密钥或其他敏感文件提交到 GitHub。

## 4. 建立长期开发规则

完善 AGENTS.md 和 CHANGELOG.md。

要求未来的每轮开发：

- 在现有软件基础上增量开发。
- 不随意删除、重写已有功能。
- 每次开发前阅读当前需求。
- 每次开发后运行相应测试。
- 记录修改文件、测试结果、用户反馈和遗留问题。
- 采用 Issue → Branch → Commit → PR → Review → Merge 的流程。

## 5. 完成 Phase 0

完成以上任务后：

1. 检查 Git Diff。
2. 运行适合本阶段的测试或静态检查。
3. 将本轮修改 Commit 到开发分支。
4. Push 到 GitHub。
5. 创建 Pull Request，并关联 Phase 0 Issue。
6. 汇报修改文件、Commit SHA、测试结果、Issue 和 PR 链接。

限制：

- 不修改现有临床业务逻辑。
- 不重置数据库。
- 不修改 C 盘备份。
- 不自动合并到 main。
- 不创建正式 Release。
- 不提交真实患者数据。

Phase 0 完成后停止，等待我审查和验收，再进入 Phase 1。
