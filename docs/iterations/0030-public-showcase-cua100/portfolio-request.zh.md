请对当前 **CareFlow EHR（Epic-inspired EHR）** 项目的 GitHub 成果展示进行全面更新。

目标：将 GitHub 仓库首页改造成专业、现代、适合 AI Engineer / Software Engineer 求职作品集展示的 README，参考我其他项目 CareConnect 3.0 的展示结构和视觉风格。

GitHub 仓库：KateK77/careflow-ehr

## 一、重新设计 README.md

参考 CareConnect 3.0 的 README 展示方式：

1. 顶部使用清晰的项目名称：CareFlow EHR。
2. 添加简洁、专业的英文产品介绍。
3. 在顶部展示最新版本的真实产品截图，优先选择主界面、医生工作台、患者病历、护士工作台和患者门户。
4. 如果已有正式可用的在线 Demo，突出展示 Open Website、Sign In 和 Demo Accounts；如果尚未部署，不得编造在线链接。
5. 介绍核心功能及系统架构。
6. 展示主要技术栈。
7. 让招聘人员进入 GitHub 后，首先看到产品是什么、能做什么，以及实际效果。

请检查目前 README 是否仍包含过时的 release-candidate、旧 PR 和旧开发状态信息，根据当前 GitHub 实际情况进行更新。

视觉风格参考 CareConnect 3.0：简洁、专业、大尺寸真实截图、合理留白、清晰的英文标题和可点击链接。

不要直接复制 CareConnect 的产品描述或图片。

## 二、在 README 首页显著展示 100 项真实 CUA 测试结果

已有的 100 项原生 CUA 测试已经完成，不要重新生成，也不要重新运行任何付费测试。

请从现有测试证据读取并展示以下真实结果：

- Model requested: GPT-5.4
- OpenAI Responses API + native ComputerToolset
- Total evaluated tasks: 100
- Passed: 85
- Failed: 15
- Overall success rate: 85%
- Read-only / authorization: 69/70 (98.57%)
- Write / clinical workflows: 16/30 (53.33%)
- API responses: 336
- Estimated token cost: $3.38 (not a verified invoice)

展示按难度分组的真实结果：

| Difficulty | Passed | Total | Success Rate |
| ---------- | ------ | ----- | ------------ |
| Level 1    | 10     | 10    | 100%         |
| Level 2    | 33     | 33    | 100%         |
| Level 3    | 26     | 27    | 96.30%       |
| Level 4    | 8      | 20    | 40%          |
| Level 5    | 8      | 10    | 80%          |

在 README 中提供清晰的入口：

- All 100 Test Cases
- Per-Task Results
- Difficulty Breakdown
- Screenshots & Action Traces
- Failure Analysis
- Evaluation Methodology
- Evidence Integrity Manifest

所有链接必须指向 GitHub 中真实存在的文件。

## 三、展示真实测试方法与局限

明确说明：

1. 测试使用 GPT-5.4 请求 OpenAI 原生 Computer Use 工具，通过实时截图生成浏览器操作。
2. Playwright 负责浏览器执行，测试框架负责数据准备、部分登录和独立断言。
3. 不能宣称所有登录、初始化和导航都是 AI 完全自主完成。
4. 公开证据包括 100 份逐项运行记录和 100 张最终截图，但不包含完整原始 API 请求/响应及全部中间截图。
5. 费用 $3.38 是 token 估算，不是经核实的 OpenAI 实际账单。
6. CF-032、CF-033、CF-034 存在源码哈希溯源不一致，须在详细审计说明中保留。
7. 85% 只代表该基准测试集的成功率，不代表系统达到临床使用或生产安全标准。

在 README 首页简洁展示主要限制，并链接到完整审计报告。

## 四、整理 GitHub 文档结构

请检查现有 `docs/testing/cua100-v1/` 和 `docs/showcase/`。

要求：

- 复用现有 100 项原始测试数据。
- 保留原始结果和失败记录。
- 不修改 PASS/FAIL、难度、API 请求次数、费用或操作轨迹。
- 不删除原始证据。
- 修复 README 中的失效链接和乱码。
- 统一截图的展示尺寸与排版。
- 将详细证据留在 docs 中，README 负责简洁、直观地展示和导航。

## 五、GitHub 更新流程

目前 CUA 成果在 `docs/public-showcase-cua100` 分支，之前对应 PR #63。

请先检查 PR #63 是否仍然开放、是否存在冲突，以及 main 的最新状态。

优先复用现有 PR #63，避免建立重复 PR。

实施流程：

1. 检查工作区是否存在未提交修改，不得覆盖。
2. 更新 README 和必要的展示文档。
3. 检查 Markdown 图片及链接。
4. 检查 README 中涉及的事实是否与原始证据一致。
5. 运行适当的免费测试及 CI。
6. Commit 并 Push 到现有 PR 分支。
7. 检查 PR CI 状态。
8. 如果所有检查通过、没有冲突，且没有未解决的审查要求，则合并 PR #63 到 main。
9. 确认 GitHub 默认分支 README 已经显示新的作品集页面及 100 项测试结果。

不得修改应用业务代码、数据库、原始 CUA 测试结果或 API Key。

不得调用任何付费 API。

## 六、完成后向我报告

请提供：

1. GitHub 首页链接。
2. PR #63 链接及最终合并状态。
3. 更新后的 README 预览。
4. 100 项测试结果入口。
5. 截图和证据入口。
6. CI 检查结果。
7. 是否存在未解决的问题。

最终目标：让招聘人员打开 CareFlow EHR GitHub 仓库，就能直观看到一个完整的医疗 EHR 软件项目、真实运行截图、主要功能，以及具有可审计证据的 GPT-5.4 原生 CUA 测试成果。补充要求：请重点优化 CareFlow EHR GitHub README 的 Live Demo 展示和 Demo Accounts 排版。

这个项目主要用于 AI Engineer / Software Engineer 求职作品集。目标是让招聘人员打开 GitHub 首页后，几秒内就知道如何体验网站，不需要阅读复杂的安装说明。

## 1. Live Demo 必须醒目

在 README 顶部产品介绍和主截图附近，设置清晰的 Live Demo 区域。

如果已部署在线网站，提供：

- Open Live Demo
- Staff Sign In
- Patient Sign In
- Demo Accounts
- Quick Walkthrough

所有链接都必须实际可访问。如果尚未部署，请明确说明部署状态，不得伪造 URL。

## 2. 提供预先注册的 Demo Accounts

在线 Demo 必须预先创建可以直接登录的测试账号。

请检查现有的角色权限系统，优先提供：

- Administrator
- Physician
- Nurse
- Front Desk
- Patient
- Pharmacist
- Laboratory Staff

如果其他角色已实现且适合展示，也可以添加。

每个账号必须：

1. 已经存在于在线 Demo 数据库。
2. 能够正常登录。
3. 具有对应角色的正确权限。
4. 使用完全虚构的姓名和患者资料。
5. 可以查看有代表性的模拟医疗数据。
6. 不需要访问者进行注册、邮箱验证或复杂配置。
7. 不使用任何真实个人账号或生产凭证。

请设计清晰的 Demo Account 表格：

| Role       | Demo Username | Demo Password | What to Explore                        |
| ---------- | ------------- | ------------- | -------------------------------------- |
| Physician  | 实际可用账号        | 实际 Demo 密码    | Patient charts, encounters, SOAP notes |
| Nurse      | 实际可用账号        | 实际 Demo 密码    | Vitals, nursing workflows              |
| Front Desk | 实际可用账号        | 实际 Demo 密码    | Registration, appointments, check-in   |
| Patient    | 实际可用账号        | 实际 Demo 密码    | Patient portal, appointments, messages |

其他角色按相同格式添加。

这里的账号和密码必须来自真实初始化的 Demo 数据，不允许填写示例占位符冒充可用账号。

公开的 Demo 密码必须是专门为公开体验设计的低权限共享凭证，绝不能与开发、管理员维护、部署或任何私人账号共用。

如果 Administrator 角色具有高权限，请不要公开完整管理员账号。可创建功能受限的展示角色，或只展示管理员功能的截图。

## 3. Demo 数据和安全

所有数据仅限合成数据。

因为账号会公开，必须防止访问者破坏其他人的体验：

- 优先使用只读展示数据或受限的模拟写入权限。
- 对写入操作提供可重置的演示数据环境。
- 禁止访问生产数据。
- 禁止公开真实 API Key、数据库密码或部署凭证。
- 禁止公共账号修改其他用户密码、提升权限或访问服务器管理功能。
- 如果部署环境存在持久数据库，请先确认 Demo 数据重置方案，不能直接清空或覆盖现有数据库。

如果暂时不能安全提供某个角色的公共账号，请明确标记为暂不可用，不能为了展示效果降低安全限制。

## 4. README 排版优化

参考 CareConnect 3.0 的简洁、现代风格。

首页前半部分建议按以下顺序：

1. CareFlow EHR — 项目名称和一句话介绍
2. 最新版大尺寸产品主截图
3. Live Demo — 醒目的体验入口
4. Demo Accounts — 清晰的账号表格
5. Quick Walkthrough — 3–5 步体验流程
6. Core Features — 核心功能
7. AI CUA Benchmark — 85/100 结果与难度统计
8. Architecture & Tech Stack
9. Full Evaluation Evidence

请特别注意：

- GitHub Markdown 排版简洁、整齐。
- 避免顶部出现大段开发历史。
- 把过时的 PR、开发阶段说明移到详细开发文档。
- 让主截图、Demo 链接、账号表格和 85% CUA 结果足够醒目。
- 使用专业英文撰写 README。
- 可以使用少量简洁的 badges，但不要堆砌装饰。
- 使用真实截图，不要生成虚假的产品 UI 图片。
- 检查桌面和手机浏览 README 时的可读性。

## 5. 验证要求

完成后请实际验证：

1. 所有 Live Demo 链接可打开。
2. 每个公开 Demo 账号都能成功登录。
3. 登录后进入正确的角色工作台。
4. 每个角色至少有一个能正常体验的代表性功能。
5. 所有截图和 README 链接有效。
6. 100 项 CUA 原始测试结果和证据完全不变。

不要运行付费 API 测试。

如果需要新部署、修改线上数据库或创建共享账号，请先报告具体方案与风险，等待我批准后再执行。可以先完成 README 的其他排版改进。

最终请更新现有 PR #63，并在安全、CI 和审查要求满足后合并到 main。

完成后提供 GitHub README 链接、在线 Demo 链接，以及已验证可用的 Demo 账号清单。
