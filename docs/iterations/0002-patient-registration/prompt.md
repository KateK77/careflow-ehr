# Approved Phase 1A prompt

CareFlow EHR 的 Phase 0 已通过验收并合并到 main。

现在正式批准启动 Phase 1A：Patient Management（患者管理）。

项目目录：\
D:\AI-Workspace\Personal\careflow-ehr

GitHub 仓库：\
KateK77/careflow-ehr

## 一、开发准备

1. 检查 Git 状态，确保当前 main 已同步 GitHub，且没有未提交的用户修改。
2. 阅读根目录 AGENTS.md、docs/architecture.md、docs/roadmap.md，以及 docs/requirements/v1.0/product-spec.md。
3. 使用现有 Django 架构，不要重新创建项目，不要切换到 React/FastAPI。
4. 创建 Phase 1A GitHub Issue，明确功能范围与验收标准。
5. 从最新 main 创建分支 phase/0002-patient-registration。
6. 按照 docs/iterations/TEMPLATE.md 建立本轮开发记录，保存本 Prompt 原文。

## 二、开发功能

### 1. 用户登录和角色权限

使用 Django Authentication 建立演示登录系统。

初期支持 Administrator、Physician、Nurse、FrontDesk 四类角色。

必须在 Django 后端验证权限，而不只是隐藏前端按钮。

建立安全的合成演示账户初始化方式，不要将演示密码硬编码进仓库。

### 2. Patient Management

建立真实数据库模型及页面，实现：

- 患者列表
- 新建患者
- 患者搜索
- 患者详情
- 编辑患者基本信息
- MRN 唯一性验证
- 潜在重复患者提醒
- 输入验证和错误提示
- 患者创建和修改审计记录

所有数据都必须保存在数据库中，不能使用仅存在于前端的静态患者列表。

### 3. 用户界面

设计原创的现代化 EHR 界面。

需要包含：

- 顶部导航栏
- 左侧功能导航
- 当前登录人员和角色
- Dashboard
- Patients 页面
- 搜索和筛选栏
- 患者表格
- 新建患者表单
- 患者详情页面
- 操作成功或失败的明确反馈

界面应具有专业医疗软件的高信息密度，但保持清晰、易操作、响应式布局。

所有页面显示 DEMO — NOT FOR CLINICAL USE。

本轮界面不复制 Epic 官方的商标、图标、CSS 或专有布局。

### 4. 合成数据

提供可重复运行的 synthetic patient seed 命令。

全部使用虚构患者数据，不接入真实医疗信息。

### 5. 测试

编写并执行自动化测试，至少覆盖：

- 登录和退出
- 用户权限
- 患者创建成功
- 患者搜索
- 患者详情访问
- MRN 重复处理
- 无效数据输入
- 未授权访问
- 审计记录

运行 python manage.py check 和 python manage.py test。

确保原有测试仍然通过。

## 三、范围限制

本轮暂时不要开发：

- 预约与排班
- 医生临床笔记
- 检验、药物和医嘱
- AI 功能
- 患者门户

不要删除或重写现有业务代码，不要清空或重置本地数据库，不要修改 C 盘备份。

## 四、开发留痕

保存本轮：

- 需求和验收标准
- 完整 Prompt
- 开发报告
- 修改文件清单
- 测试结果
- Git Commit SHA
- GitHub Issue 和 PR 链接
- 已知问题

开发完成后提交到当前功能分支，Push 并创建 PR。

等待 GitHub Actions 检查完成。

不要自动合并到 main，不要创建正式 Release。

## 五、最终交付

请提供：

1. 软件实际运行和访问方法
2. 已实现功能及页面
3. 可以测试的合成演示账户使用说明
4. 数据库模型和迁移说明
5. 自动化测试结果
6. GitHub Issue、Commit 和 PR 链接
7. 尚未完成的功能和已知问题

完成后停止，等待我亲自运行软件、提供反馈和验收。
