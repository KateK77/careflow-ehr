# CareFlow EHR：Epic-inspired 医疗信息系统完整产品规格（v1.0）

> 文档定位：独立构建的、功能上参考 Epic 常见临床工作流程的 **原创 EHR 教学与演示系统**，不是 Epic 官方软件，也不是与 Epic 接口兼容性的保证。创建日期：2026-11-06。
> 数据边界：**只允许合成/虚构患者数据；所有画面有 DEMO / NOT FOR CLINICAL USE 标识；不得用于真实诊疗、处方、给药、计费、患者隐私处理。**
> 对标依据：Epic 官方软件产品目录、专科/住院/患者体验/预约/互联/AI 官方资料，以及医疗机构公开的培训概述。不同医院 Epic 界面和启用模块不同；以下为研发目标、不是 Epic 的逐像素或逐字段内部产品文档。

## 0. 总体目标和成功定义

创建一套能在浏览器中交互使用的全栈电子健康记录（EHR）软件，供门诊医生、住院医生、护士、接待/排班人员、药师、实验室工作人员、影像科、账单人员、系统管理员及患者分别使用。同一个患者记录应贯穿预约→登记→就诊→诊断→笔记→医嘱→检验结果→随访/出院→患者门户；每个操作必须更新真正的数据库、操作状态以及相关人员任务队列。**不接受静态页面或纯假按钮。**

### 原则
1. 临床记录是核心：以 `Patient`、`Encounter` 和纵向时间线为中心。
2. 多角色用户界面：每个角色只看到其有权访问的工作台；前后端双层鉴权。
3. 状态可追踪：每个医嘱/笔记/检验/预约/用药动作可追踪状态、时间、操作者。
4. 可演示：预置合成患者、演示人员、就诊案例、化验、处方、消息和账单；所有关键路径可点击。
5. 原创品牌和布局：产品名称 `CareFlow EHR`，禁止冒用 Epic / MyChart 徽标、商标、截图、CSS 或声称与其合作。
6. 先闭环再广度：第一期重点门诊；其他模块逐阶段接入相同数据模型。
7. 安全：非生产临床使用；禁止外部真实电子处方、真实保险交易、真实结果接口和真实 PHI；AI 的一切临床建议必须标注草稿并由人确认。

## 1. 系统模块总体清单

### 1.1 P0：平台基座
- 登录、退出、演示账户、角色切换（管理员可模拟其他角色），用户资料、机构/院区/科室/诊室。
- 用户角色：Administrator、Physician、Nurse、FrontDesk、Pharmacist、LabTech、Radiologist、BillingStaff、Patient；可以给用户多个角色。
- 患者全局搜索（姓名/MRN/生日/电话），患者新建、重复记录提醒，操作审计。
- 全局搜索、通知、任务计数、快捷动作、收藏患者、最近打开的患者。

### 1.2 门诊（EpicCare Ambulatory 类工作流）
- 医生日程：按日/周、医生/科室筛选，预约状态 scheduled/arrived/roomed/in-progress/completed/cancelled/no-show。
- Registration / Check-in：人口统计学、联系电话、紧急联系人、保险（模拟）、患者同意勾选（演示），签入与分诊。
- Rooming：主诉、生命体征、过敏史、当前药物、病史、筛查问卷、完成待诊标记。
- Visit Navigator：按步骤记录病史、复核问题/过敏/药物、写 SOAP 或 H&P、诊断关联、下医嘱、Patient Instructions、完成访问。
- 诊断：长期 Problem List 与单次 Encounter Diagnoses 分离，ICD-10/SNOMED 作为可搜索模拟目录；状态、起止日期、备注。
- 电子病历笔记：新建、自动保存、草稿、修订、签署、追加签署补充；模板化 HPI、ROS、Exam、Assessment、Plan。
- SmartTools 风格：自定义 dot phrase 模板（如 `.followup`），变量插值（患者名、最新生命体征）、选项型内容片段、常用医嘱集；自行设计实现，不复制 Epic 专有配置。
- 患者就诊总结 AVS：诊断、药物、检查、随访、个性化说明，可展示打印预览，患者门户同步。

### 1.3 患者纵向病历 / Chart Review
- Patient Snapshot：头像占位/姓名、MRN、出生日期/年龄、性别、目前就诊、过敏、护理警示、问题、药物、历史、最近生命体征。
- Chart Review tabs：Overview、Timeline、Encounters、Notes、Problems、Allergies、Medications、Labs、Imaging、Procedures、Immunizations、Documents、Care Plans。
- 时间线支持事件类型/日期筛选、按日期分组、详情抽屉；每个记录显示作者、时间、所属就诊、来源和签署状态。
- 检验数值支持列表/趋势图/参考区间/异常高低值标签；保留单位、样本/采集时间。
- 药物核对：正在使用/历史停用/患者报告，核对者、时间、状态；不等同真实处方发放。
- 过敏：过敏原、反应、严重程度、备注、记录者、复核状态；未知过敏与明确无已知过敏不应混淆。

### 1.4 临床医嘱 / Orders
- 分类：Laboratory、Imaging、Medication（模拟）、Procedure、Referral、Nursing、Other。
- 订单构建器：搜索目录→选择项目→指定诊断关联→输入优先级/时间/细节→预览→提交。
- 订单状态：draft→signed→queued→in-progress→completed，支持取消/拒绝/失败的分支，显示状态历史。
- 医嘱集：按临床情境预定义多条候选订单，允许逐项检查和删改，不能未经确认即全部提交。
- 模拟用药订单：药品、剂型、强度、剂量、途径、频次、持续时间、数量、模拟药房、说明；警告示意、需要医师签署。
- 订单跟踪：所有订单列表，按类型/优先级/状态/患者筛选；订单详情与其结果链路。
- **禁止**连接真实药房或向患者发放真实处方。

### 1.5 检验室 / Laboratory（Beaker 类工作流）
- 检验工作队列：已下单→待采样→已采样→已接收→处理中→待审核→结果发布/已取消。
- 标本跟踪：标本类型、模拟条码、采集/接收/处理时间、采样者、拒收理由。
- 录入检测项目：数值、单位、参考范围、异常标记、评论，支持多分析物面板（CBC/BMP/HbA1c 示例）。
- 模拟结果复核、发布；医生 Chart Review / Inbox 立刻可见；异常结果进入提醒队列。
- 不自动推断治疗建议；临界值仅作为测试用例演示视觉提醒。

### 1.6 放射影像 / Radiology（Radiant 类工作流）
- Imaging Orders / Worklist：未排期、已排期、已签到、检查进行中、待报告、最终报告。
- 检查属性：modality (X-ray/CT/MRI/US)、部位、对比剂标记（不建议剂量）、预约时间、检查状态。
- 结果报告：Findings、Impression、报告医师、签署时间；附演示用占位图片，无真实 DICOM 系统要求。
- 可从医生病历查看影像报告、结果历史和状态。

### 1.7 住院 / Inpatient（EpicCare Inpatient 类）
- Admission/Discharge/Transfer：住院申请、入院、病区/床号分配、转科转床、出院；可视化床位容量。
- 患者列表：按科室/病区/主治医师排序，LOS、诊断、待办、警示。
- 住院摘要：住院天数、护理团队、生命体征趋势、Active Orders、进出量 I/O、Care Plan、病程笔记、结果。
- 查房清单：每日任务、待签医嘱、结果、会诊、出院计划。
- Discharge Workflow：出院诊断、出院说明、模拟药物清单、随访安排、出院总结；在所有必需项完成后状态 closed。

### 1.8 护理 / Nursing + MAR
- Nurse Worklist：病床列表、今日待办、需要采集生命体征、待确认医嘱、用药计划、交班任务。
- 护理评估：疼痛、跌倒风险、意识状态、体温、心率、呼吸频率、血压、血氧、身高体重、症状、护理备注。
- Flowsheets：行=指标，列=时间段；支持编辑、备注、单次趋势查看；保留单位和记录人。
- Medication Administration Record：模拟用药计划时间轴与给药事件；Scheduled / Given / Held / Refused / Missed；动作需给药人、时间、理由，并有不可变审计。
- Care Plans：目标、干预、负责人、进度；交班 SBAR（Situation/Background/Assessment/Recommendation）总结。
- **高风险给药模拟**：默认明确注明模拟环境，不能发起真实给药行为或真实扫码给药。

### 1.9 急诊 / Emergency（ASAP 类）
- ED Tracking Board：列表示意按 Waiting→Triage→Roomed→Provider→Observation→Discharged/Admitted；紧急程度、等待时间、床位、责任医生。
- 分诊：到达方式、主诉、紧急程度、初始生命体征、主要风险标记、随访动作。
- 急诊笔记、检查医嘱、结果观察、Disposition (discharge/admit/transfer)；流转记录。
- 看板支持排序、筛选、刷新、聚合计数；不实现真实急诊医学判断算法。

### 1.10 药房 / Pharmacy（Willow 类）
- 药师队列：待审核、已审核、需澄清、已拒绝、已取消模拟药物订单。
- 展示药名、剂型、强度、途径、数量、拟定给药时间、患者过敏提醒、订单医师。
- 审核操作保留备注，状态推送至医生订单页、MAR；模拟库存/调剂状态。
- 仅演示订单工作流，不与任何电子处方、药房仓储或受控药品外部网络连接。

### 1.11 In Basket / 协作消息
- 任务类别：Patient Message、Result Notification、Refill Request（模拟）、Referral、Staff Message、Cosign、Chart Completion。
- 文件夹：Inbox / Assigned / Sent / Completed / Archived；搜索、筛选、优先级、未读状态、指派。
- 消息线程：发件人、关联患者/就诊、上下文摘要、附件占位、回复模板、关闭任务。
- 对异常检验的 `Result Notification`，支持点击跳到病历并标记“已审阅”。

### 1.12 患者门户（MyChart 类，但**必须原创命名**）
- 患者只能访问关联自己的记录；账户登录、个人信息与通知设置。
- Dashboard：接下来的预约、最近检测结果、药物列表、未读消息、待付费用、待完成问卷。
- Appointments：查看可约时段、预约/取消/重新预约；访问说明、模拟远程就诊链接占位。
- Test Results：按时间列示结果，支持异常值说明但不可替代专业解读。
- Messages：发送非紧急消息给诊疗团队（演示）；避免表现为真实应急通道。
- Medications：查看历史和当前药物记录、提交模拟续方请求。
- Billing：查看账单、模拟支付结果，不连接支付网关。
- After Visit Summary / Forms / Proxy access（代理访问仅后期实现）。

### 1.13 前台、财务与收入周期（Cadence、Resolute 类）
- Registration：人口统计学、保险模拟信息、紧急联系人、担保人、资格核验占位。
- Scheduling：按医生/诊室/日期的日程网格，预约创建/改期/取消/候补、冲突检测。
- Patient Flow：待签到、已签到、已分诊、就诊中、完成、未到诊状态。
- Billing：就诊项目、模拟收费编码、费用项、账单、保险理赔模拟状态、付款模拟交易。
- 不向实际保险机构传送 Claim，也不收取真实费用。

### 1.14 人群健康 / Analytics（Healthy Planet / SlicerDicer 类）
- Cohort Builder：按年龄范围、时间、诊断、药物、检验结果、是否按期随访过滤匿名合成人群。
- Dashboard：患者数量、今日到诊/未到诊、未完成医嘱、异常检验结果、出院数；各模块指标。
- Care Gaps：模拟尚未完成的筛查或预约任务；可创建 outreach task，避免用演示规则作医学建议。
- 导出 CSV（仅合成数据）、日期筛选、条形/折线图、角色授权。

### 1.15 医疗数据互通（FHIR-inspired）
- 内部统一数据模型；标准数据导出方向兼容 FHIR R4 资源含 Patient、Encounter、Observation、Condition、AllergyIntolerance、MedicationRequest、DiagnosticReport、Appointment、Practitioner、DocumentReference。
- 第一阶段只提供内部 REST API；后续可新增 `/fhir/Patient/{id}` 等读取型演示接口、数据映射和 JSON 校验。
- `Care Everywhere` 指跨机构交换能力；**不要将本项目标记为 Epic Care Everywhere 真实接入，也不要声称符合认证。**

### 1.16 AI 临床辅助（参考 Epic Art 的功能类别，自主实现）
- AI Chart Summary：按患者历史/医嘱/最近结果生成含来源链接的摘要，不能虚构无来源的病史。
- AI Note Draft：根据用户明确输入的模拟就诊文本生成 SOAP 草稿，医生手动审阅/修订/签署。
- Inbox Reply Draft：消息回复草稿，永远不自动发送。
- Clinical Timeline Q&A：检索患者模拟记录、给出带引用的答案；未找到依据时说明缺失。
- Explain Result：对测试结果做通俗术语解释，非医疗诊断/治疗建议。
- AI 生成内容必须标明 `AI-generated draft`、显示引用、请求确认；无真实患者信息上传云端。

### 1.17 后期专科扩展（不纳入首次交付）
- Oncology：肿瘤分期、方案/周期追踪（不实现真实化疗剂量推荐）。
- Surgery/Anesthesia：手术排期、术前核对清单、术中事件、术后恢复笔记。
- Cardiology：ECG 检查、超声心动图结构化报告。
- Obstetrics：孕期访视、母婴关联、分娩过程事件。
- Dermatology / Dentistry / Ophthalmology / Orthopedics / Nephrology / Endoscopy / Transplant 采用插件式专科工作区追加。

## 2. 详细界面设计系统（所有界面均为原创）

### 2.1 设计系统
- 目标：桌面优先，1440×900 最佳；支持 1280 宽度，并在平板上将侧栏折叠。患者门户移动优先。
- 视觉：浅色中性背景、清晰网格、低饱和蓝/青强调色、灰色表格边框、统一字号；禁止复制 Epic 的图标/图形资产。
- 顶部 Global Header：高度约 56 px；Logo、组织、角色、搜索、通知、任务、个人菜单、DEMO 徽标。
- 左侧 App Navigation：宽约 210–230 px；可折叠；随角色出现不同菜单。
- 在患者详情中：左侧 Patient Summary/Storyboard（约 250–280 px）、中部 Workspace（伸缩）、可展开右侧 Context Drawer（约 320 px）。
- 工作区顶部：患者姓名+MRN+年龄+身份、过敏/安全标记、所属 Encounter、临床状态、选项卡；底部固定操作栏：Save Draft、Sign、Complete 等（按权限显示）。
- 基本控件：Table、DataGrid、Tabs、Search ComboBox、DatePicker、Status Tag、Inline Editor、Modal、Drawer、Toast、Validation Errors、Command Palette、Confirm Dialog、Skeleton、Empty State。
- 状态示例：草稿=灰；进行中=蓝；已完成=绿；警示=琥珀；异常关键结果=红（有文本，不能只靠颜色区分）。
- UX：表格支持排序/筛选/分页，保存状态清楚可见，临床签署必须明确确认；键盘可访问，标签/ARIA、Focus 明确，支持浏览器缩放。
- 除患者门户外，患者背景信息应始终可快速访问，以免上下文丢失。

### 2.2 全局布局示意（不是 Epic 原始像素布局）
```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CareFlow EHR  [Organization] [Global Search]     [Alerts 3] [Inbox 8] [Dr. Demo] │
├──────────────┬─────────────────────────────────────────────────────────────────────┤
│ Home         │ Patient: Sarah Johnson | MRN D-1001 | Visit: In Progress           │
│ Schedule     ├───────────────────┬─────────────────────────────────────────────────┤
│ Patients     │ Story Panel       │ Workspace Tabs: Summary / Chart / Notes / ...   │
│ Inbox        │ Age / DOB / MRN   │ ┌─────────────────────────────────────────────┐ │
│ Orders       │ Allergies         │ │ Main lists, forms, trends, note editor     │ │
│ Lab          │ Active Problems   │ │                                             │ │
│ Radiology    │ Current Meds      │ │                                             │ │
│ ED           │ Latest Vitals     │ │                                             │ │
│ Inpatient    │ Alerts & CareTeam │ └─────────────────────────────────────────────┘ │
│ Analytics    │                   │ [Save Draft]   [Review]   [Sign]  [Close Visit]│
├──────────────┴───────────────────┴─────────────────────────────────────────────────┤
│ DEMO ONLY • Synthetic patient data • Not for clinical use                         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 每一页的具体页面元素与动作（页面 S01–S27）

#### S01 登录 / 角色选择 `/login`
- 左边：产品说明、演示系统声明；右边：Email、Password、Sign In；示例账户快速选择（仅 dev seed）。
- 成功登录后进入匹配角色的默认工作台；错误显示通用错误并记录审计；绝不能在 UI 直接显示生产凭证。

#### S02 医生 Dashboard `/app/dashboard`
- 顶部 KPI：Today's Appointments、Patients Waiting、Unsigned Notes、Unreviewed Results、Inbox Count。
- 左栏 Today Schedule 表：time、patient、age、visit type、status、room、action(Open Chart)。
- 右栏 Action Center：Urgent Results（模拟）、Open Tasks、Recent Charts、Quick Create Note。
- 点击行应打开患者正确 Encounter；点击 KPI 应进入筛选后的对应页面。

#### S03 患者搜索 `/app/patients`
- SearchBar（姓名/MRN/生日）、高级筛选、New Patient、患者列表。
- 表格列：MRN、Name、DOB、Age、Sex、Last Encounter、Primary Doctor、Actions。
- Click patient→S06；New Patient→S04；有精确重复 MRN 必须报错。

#### S04 患者注册/编辑 `/app/patients/new`、`/app/patients/:id/edit`
- Stepper：Identity、Contact、Emergency Contact、Coverage（mock）、Review。
- 必填：姓名、生日、性别/性别记录、联系方式（可选策略）、演示 MRN（可自动生成）。
- Validations：生日不能未来、重复匹配提示；保存后进入患者 Snapshot；编辑记录 actor/time。

#### S05 Schedule `/app/schedule`
- 顶部视图切换 Day/Week、Date Picker、Provider、Department、Visit Type；右上 New Appointment。
- 时间网格纵轴 08:00–18:00，横轴诊室/医生；预约块显示姓名、状态、时间。
- 预约弹窗：选患者、医生、日期时段、时长、类型、理由；冲突阻止；支持 reschedule/cancel/check in。

#### S06 Patient Snapshot `/app/patients/:id/summary`
- 顶部身份栏；Story Panel 卡片：allergies、conditions、medications、vitals、care team、warnings。
- 主区大卡片：Recent Encounters、Clinical Timeline、Latest Labs、Active Orders、Care Gaps、Care Team。
- 所有卡片均有 `View All` 跳到对应 tabs；缺数据时明确显示 No data，不伪造。

#### S07 Chart Review `/app/patients/:id/chart`
- 上方 tabs：Overview、Encounters、Notes、Problems、Allergies、Medications、Results、Imaging、Documents、Immunizations。
- 左侧过滤：time range、type、provider、status；中心 timeline/table；右侧点击行弹出 detail。
- Lab results 增加 trend chart、reference range、unit、critical flag；可按时间导出模拟 CSV。

#### S08 Encounter / Visit Navigator `/app/encounters/:id`
- 左侧步骤导航：Rooming、Chief Complaint、History、Problems、Medication Reconciliation、Allergy Review、Vitals、Review of Systems、Physical Exam、Diagnoses、Orders、Notes、Instructions、Wrap-up。
- 每项状态：Not Started / In Progress / Complete；主区是对应编辑器；底部 Next / Previous / Save Draft / Complete Encounter。
- 完成就诊前校验必需项：至少 1 个诊断、必要笔记签署或显示未完成警告、待签订单提示；不能无提示一键完成。

#### S09 Rooming & Vitals `/app/encounters/:id/rooming`
- 头部患者和预约信息；表单：主诉、BP systolic/diastolic、pulse、resp、temp、SpO2、height、weight、pain、time。
- 显示历史生命体征、趋势，临床人员记录/修订时均记录来源。
- 过敏/药物核对每项含 `Reviewed by / time`；操作后更新完成状态。

#### S10 Note Editor `/app/encounters/:id/notes/new` 和 `.../notes/:noteId`
- 顶部：Note Type（SOAP/H&P/Progress/Discharge）、Author、Status Draft、Save Indicator、Template Picker。
- 表单字段：Chief Complaint、HPI、ROS、History、Exam、Assessment、Plan、Follow-up；也可切换自由文本。
- 功能：Insert Template、Dot Phrase Autocomplete、Insert Latest Vitals、Preview、Autosave、Save Draft、Sign (confirm)。
- 签署后不可无痕覆盖；创建 addendum；显示签署时间/版本；AI Draft（后期）需要来源和审阅。

#### S11 Diagnoses & Problem List `/app/patients/:id/problems`
- 分 tabs：Longitudinal Problems / Visit Diagnoses；搜索添加 ICD-10/SNOMED 字典中的模拟条目。
- 列：code、description、onset、status、priority、linked encounter、documented by；可标为 resolved。
- 访视诊断和长期问题分别管理；添加一个并不自动强制同步另一个。

#### S12 Medications & Allergies `/app/patients/:id/medications`、`/allergies`
- Medication Table：Active / Historical / Patient-reported；name、sig、route、frequency、start/end、status、reconciled。
- Allergy Table：substance、reaction、severity、recorded at、verified；支持明确 `Unknown`/`None documented`。
- 操作：Add/Edit/Discontinue/Mark Reviewed；模拟数据不与外部药房同步。

#### S13 Order Composer `/app/encounters/:id/orders/new`
- 两列：左侧分类与 Catalog Search，中区 Results；选择项后右侧 Order Detail Drawer。
- 详情：type、name/code、priority、desired date、indication、ordering provider；药物额外 route/dose/frequency/quantity/simulated pharmacy。
- 按钮：Add to Draft Queue→Review Queue→Sign/Submit；支持 Remove、Edit、Cancel；签署前检查关联患者与就诊。
- 页面顶部显示 Allergy Context 和重复订单提醒（演示规则）；任何警告应可展开解释。

#### S14 Active Orders `/app/patients/:id/orders`
- Tabs All/Labs/Medications/Imaging/Referrals；筛选 status/time/provider。
- 列：order#、type、display、created、priority、status、owner、details；点击查看事件时间线，允许符合权限的 cancel/acknowledge。

#### S15 Lab Workbench `/app/lab`
- 左侧状态队列 counts、中央 Worklist、右侧样本详情与结果输入。
- Worklist 字段：Specimen ID、Patient、Tests、Collection Time、Priority、Status。
- 结果表格：analyte、value、unit、range、flag；支持保存草稿、审核、发布，发布后进入 Chart Review & Inbox。

#### S16 Results Review `/app/results`
- 结果队列：My Patients / Unreviewed / Abnormal / All；患者、order、time、value、flag。
- 右侧结果细节与趋势；按钮 Mark Reviewed、Open Chart、Message Team；审阅时间/人持久化。

#### S17 Radiology Worklist `/app/radiology`
- 检查队列和预约、modality、patient、status；详情页有检查元信息、演示图像/文件占位、报告 Findings/Impression。
- 报告草稿→最终签署后，医生在病历和 Inbox 查看。

#### S18 Inpatient Patient List `/app/inpatient`
- 病区筛选、床位列表/表格；列：Bed、Patient、Admitted、LOS、Attending、Primary Diagnosis、Open Tasks。
- 动作：Admit、Assign/Move Bed、Transfer、Open Chart、Start Discharge；点击床位查看 occupancy。

#### S19 Nurse Worklist & Flowsheets `/app/nursing`
- Tabs：Assigned Patients、Assessments、Flowsheets、Care Plans、Handoff。
- Flowsheets Grid：固定测量项、时间列、数值编辑单元格；支持新增时间点；弹出记录详情。
- Nursing Assessment：Vitals、Pain、Fall Risk、Neuro、Skin、I/O、Notes；保存后纵向时间线同步。

#### S20 MAR `/app/mar`
- 过滤：unit、patient、time window（Due Now / Next 4 Hours / All）；药物行 x 时间列。
- 每一格表示模拟计划事件，状态：Scheduled/Recorded Given/Held/Refused/Missed。
- 点击格子弹窗：record action、actual time、dose as ordered（只读默认）、reason、co-sign mock；保存不可无痕覆盖。

#### S21 ED Tracking Board `/app/ed`
- 可切换 Kanban/Table；患者卡：triage level、chief complaint、arrival、waiting time、room、assigned clinician、status。
- 按状态分区；创建 ED Encounter/分诊/分配诊室/患者离院；每次流转更新历史与计数。

#### S22 Pharmacy Verification Queue `/app/pharmacy`
- 订单表：Patient、Medication、Dose、Route、Ordering Provider、Status、Allergy Alert；详情显示风险与历史模拟说明。
- 验证/澄清/拒绝操作必须记录 actor/time/reason；同步订单状态；没有真实配药流程。

#### S23 Inbox `/app/inbox`
- 三栏：Folders & Filters / Message List / Thread Detail；unread badge、优先级、关联患者链接。
- 操作：open, mark read, reply draft, send internally, assign, complete, archive；结果提醒可 `Mark Reviewed`。

#### S24 Patient Portal `/portal`
- 与临床端独立布局：顶部简洁导航 Home、Appointments、Test Results、Messages、Medications、Bills、Visit Summaries。
- 首页卡：Upcoming Appointment、Recent Results、Tasks、Messages；页面内绝不显示其他患者的任何记录。
- 模拟预约和消息创建后，应能在 Staff Scheduling/Inbox 出现对应项。

#### S25 Billing & Registration `/app/billing`
- Billing List：Patient、Encounter、Charges、Amount、Insurance (mock)、Statement Status、Payment Status。
- Itemized bill、创建模拟费用条目、生成模拟账单、记录模拟支付、导出演示收据。

#### S26 Analytics `/app/analytics`
- KPI、time filters、diagnosis/clinic cohorts、可排序结果表、趋势图；只使用合成记录。
- Dashboard cards：Patients Served、Appointments、Pending Orders、Turnaround Time（基于模拟事件计算）等。

#### S27 Admin & Audit `/app/admin`
- Users/Roles、Clinic Setup、Catalog Setup、Note Templates、Audit Log、Demo Reset。
- Audit Log 表：timestamp、actor、role、action、resource、resource ID、summary、outcome；支持筛选，不允许普通用户删除。
- 能查看未授权访问被拒记录；管理员界面必须受后端鉴权约束。

### 2.4 交互统一要求
- Save：持久化、校验、Toast 成功、updatedAt 更新，刷新后仍存在。
- Sign：二次确认、作者、签署时间、状态不可无痕修改；只能创建新版本/补充。
- Search/Filter：服务端或受控分页，支持空状态、清除筛选。
- Cancel：只能取消具备允许状态的项目，必须提供原因，保留审计。
- Context：任何临床动作需绑定 patientId 和 encounterId，防止患者上下文串错。
- Error：网络失败显示 Retry；403 提示权限不足；404 显示 Not Found；409 显示冲突，不能静默吞掉失败。
- 无权限操作从 UI 隐藏，且 API 一律执行权限验证。

## 3. 领域模型：关系、实体与关键字段

### 3.1 身份与基础资源
- `Organization(id,name)`、`Facility(id,organizationId,name)`、`Department(id,facilityId,name,type)`、`Room(id,departmentId,name)`、`Bed(id,roomId,label,status)`。
- `User(id,email,passwordHash,displayName,roles,status,departmentId)`、`Role(id,key)`、`UserRole(userId,roleId)`、`Practitioner(id,userId,credentials,specialty)`。
- `Patient(id,mrn,firstName,lastName,dob,sex,genderIdentity?,phone?,email?,address?,emergencyContact?,createdAt,updatedAt)`。
- `Coverage(id,patientId,payerNameMock,memberIdMock,status)`；永远使用虚构 ID。

### 3.2 就诊与记录
- `Appointment(id,patientId,practitionerId,departmentId,startAt,endAt,type,reason,status)`。
- `Encounter(id,patientId,appointmentId?,type,departmentId,practitionerId,startAt,endAt?,status,chiefComplaint)`。
- `Admission(id,encounterId,bedId,admitAt,dischargeAt?,state)`、`Transfer(id,admissionId,fromBedId,toBedId,at,reason)`。
- `ClinicalNote(id,patientId,encounterId,authorId,type,structuredSections,content,status,version,signedAt?,updatedAt)` + `NoteAddendum(id,noteId,authorId,text,signedAt)`。
- `Condition(id,patientId,encounterId?,codeSystem,code,display,clinicalStatus,onsetDate?,resolvedDate?)`。
- `Allergy(id,patientId,substance,reaction,severity,status,verifiedBy?,verifiedAt?)`。
- `MedicationStatement(id,patientId,name,doseText,route,frequency,startAt?,endAt?,status,source)`。
- `VitalObservation(id,patientId,encounterId,type,value,unit,observedAt,recordedBy)`；BP 可用 systolic/diastolic 独立值统一归组。
- `CarePlan(id,patientId,encounterId?,goal,interventions,status,ownerId)`、`CareTask(id,patientId,encounterId?,type,title,dueAt?,status,assigneeId)`。

### 3.3 医嘱与结果
- `Order(id,patientId,encounterId,category,catalogItemId,orderedBy,indication?,priority,status,detailsJson,signedAt?)`。
- `OrderEvent(id,orderId,previousStatus,nextStatus,actorId,occurredAt,reason?)`。
- `Specimen(id,labOrderId,accessionNumber,type,collectedAt?,receivedAt?,status)`。
- `LabResult(id,orderId,specimenId?,analyte,valueNumeric?,valueText?,unit?,refLow?,refHigh?,abnormalFlag?,status,resultedAt?,verifiedBy?)`。
- `ImagingStudy(id,orderId,modality,bodySite,scheduledAt?,status)`、`ImagingReport(id,studyId,findings,impression,authorId,status,signedAt?)`。
- `MedicationRequest(id,orderId,name,strength,dose,route,frequency,duration?,quantity?,simulatedPharmacy?,verificationStatus)`。
- `MedicationAdministration(id,medRequestId,patientId,encounterId,scheduledAt,administeredAt?,status,recordedBy?,reason?)`。

### 3.4 交流、账单、治理
- `InboxThread(id,patientId?,encounterId?,category,subject,priority,status,createdBy,assignedTo?)`、`InboxMessage(id,threadId,senderId,body,createdAt,isRead)`。
- `Invoice(id,patientId,encounterId,amountCents,status)`、`ChargeItem(id,invoiceId,description,amountCents,codeMock)`、`MockPayment(id,invoiceId,amountCents,at,status)`。
- `AuditEvent(id,actorId,action,resourceType,resourceId,patientId?,occurredAt,detailsJson,outcome)`。
- `NoteTemplate(id,name,shortcut,body,ownerId?,isShared)`、`OrderCatalogItem(id,type,name,code?,description?,fieldsSchema)`。
- `AiDraft(id,patientId,encounterId?,kind,content,sourceRefsJson,modelLabel?,status,reviewedBy?)`。

### 3.5 状态机约束
- Appointment: `scheduled → arrived → roomed → in_progress → completed`；另有 `cancelled`、`no_show` 分支，禁止取消已完成预约。
- Encounter: `planned → in_progress → completed → closed`；必须关联 patient。
- Note: `draft → signed`；签署后更改仅用 addendum/version 记录。
- Order: `draft → signed → queued → in_progress → completed`；`cancelled/rejected` 记录原因。
- Lab: `ordered → collected → received → processing → verified → released`；结果发布前不可标记完成。
- Invoice: `draft → issued → partially_paid/paid/void`；mock payment 不是真实收款。
- 所有更改都用 UTC 存储，UI 根据配置的医院本地时区显示；跨日预约要测试。

## 4. 角色权限（初始策略）

| 行为 | Physician | Nurse | FrontDesk | Pharmacist | LabTech | Billing | Patient | Admin |
|---|---|---|---|---|---|---|---|---|
| 患者搜索/图表 | R/W-limited | R/W-limited | Demographics | relevant chart R | relevant orders R | financial subset | self only | config + audited |
| 创建/签署笔记 | Own W/Sign | Nursing note W | — | — | — | — | — | — |
| 下/签医嘱 | W/Sign | scoped order acknowledgment | — | verify med | process lab | — | — | — |
| 生命体征与 MAR | view | W | — | review | — | — | own results R | — |
| 预约签到 | read | rooming | W | — | — | — | self schedule | configure |
| 消息 | W | W | scheduling | pharmacy | results | billing | self only | audit |
| 账单 | limited view | — | registration | — | — | W | own view/mock pay | config |
| 用户/权限配置 | — | — | — | — | — | — | — | W |

注：真正生产 EHR 还需要更细粒度的访问控制、break-glass 工作流、数据分区和安全认证，此文档只是演示权限基线。

## 5. 必须跑通的端到端业务流程（E2E）

**W01 典型门诊闭环**：FrontDesk 注册虚构患者→预约时间→Check-in→Nurse 记录生命体征和药物/过敏核对→Physician 打开访视、查看历史、添加诊断、SOAP 笔记→创建 HbA1c lab order→签署订单和笔记→生成 AVS→完成就诊→Patient Portal 查看 AVS。验证每一步在数据库持久化，事件作者正确。

**W02 检验结果闭环**：医生 lab order→Lab Queue 出现→标记采样、接收、处理→录入 HbA1c 7.1%（演示值）→验证并发布→医生 Inbox 新增 Result Notification→Chart Review 显示结果→医生 Mark Reviewed→消息任务关闭。

**W03 模拟药物工作流**：Physician 创建 Medication Order→显示已知过敏警示→确认/修改模拟处方→提交给 Pharmacy Review→药师 Approve 或 Clarify→订单状态同步→Nurse MAR 展示计划项→记录模拟给药/暂停理由→审计日志可查。

**W04 住院流程**：创建 inpatient encounter→分配病床→记录护理 assessment 和每日 note→检查/结果→模拟转床→出院总结与 AVS→释放床位→患者门户显示出院摘要。

**W05 患者门户消息**：Patient 发送非紧急消息→医生 Inbox 出现→医生回复→Patient Portal 可见→双方保留线程。

**W06 预约冲突**：同一医生同一时段存在 appointment，重复提交应返回 409，UI 显示可理解错误；改期恢复。

**W07 医疗记录访问隔离**：Patient A 登录无法通过路由或 API 读取 Patient B；FrontDesk 无法签署诊疗笔记；所有拒绝记录审计。

**W08 临床签署不可变性**：签署的 note 不可被静默更改；addendum 独立记录签署人和时间；普通用户无法删除审计事件。

**W09 ED 流转**：急诊患者 arriving→triage→roomed→provider→discharged/admitted，tracking board 计数实时同步。

**W10 账单闭环**：完成访视→账单人员录入模拟收费→生成 Statement→患者门户查看→模拟支付→状态 Paid，保证不接真实网关。

**W11 Analytics**：新增合成患者/完成预约/发布结果后 dashboard KPI 能随着数据库变化，不允许硬编码固定数值。

**W12 AI 来源可追溯**：AI Summary 仅引用患者当前可访问数据，点击引用跳原记录；AI 内容不能自动签署或下单。

## 6. 技术架构建议

### 6.1 推荐技术栈（Codex 可依实际本机版本微调）
- Web Frontend：React + TypeScript + Next.js、Tailwind CSS、shadcn/ui 或等效可访问组件、React Query、Zod、React Hook Form、Recharts。
- API Backend：Python FastAPI + Pydantic + SQLAlchemy + Alembic；有自动生成的 OpenAPI 文档。
- Database：PostgreSQL（Docker Compose 本地）；如本机无 Docker，可先用 SQLite 开发，后续迁移 PostgreSQL。
- Auth：安全 Session 或 HttpOnly cookie/JWT 短期方案；密码 Argon2 hash；后端 RBAC policy；demo seed 账户仅开发环境。
- Tests：Pytest API integration、Vitest UI、Playwright E2E；lint / formatter / typecheck。
- 独立前后端的类型契约由 OpenAPI 自动生成或共享 schema 统一维护。
- 环境变量：`.env.example`，真实机密不进入 Git，mock AI adapter 默认无外部 API Key。

### 6.2 初始目录约定（Codex 需先查看当前工作区，绝不覆盖其他项目）
```
careflow-ehr/
  README.md
  AGENTS.md
  docs/
    product-spec.md
    architecture.md
    screens.md
    api.md
  apps/
    web/                 # Next.js / TypeScript UI
    api/                 # FastAPI / Python REST API
  packages/              # optional shared schemas
  scripts/
    seed_demo_data.py
  tests/
  docker-compose.yml
  .env.example
```

### 6.3 推荐内部 API 资源（示例，不要求一次性做完）
- `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
- `GET /patients`, `POST /patients`, `GET /patients/{id}`, `PATCH /patients/{id}`
- `GET /appointments`, `POST /appointments`, `PATCH /appointments/{id}`
- `GET /encounters`, `POST /encounters`, `GET /encounters/{id}`, `PATCH /encounters/{id}`
- `GET /patients/{id}/timeline`, `GET/POST /patients/{id}/conditions`, `/allergies`, `/medications`, `/observations`
- `GET/POST /encounters/{id}/notes`, `POST /notes/{id}/sign`, `POST /notes/{id}/addenda`
- `GET/POST /encounters/{id}/orders`, `POST /orders/{id}/sign`, `POST /orders/{id}/cancel`
- `GET /lab/worklist`, `POST /lab/orders/{id}/specimens`, `POST /lab/orders/{id}/results`, `POST /lab/results/{id}/release`
- `GET /inbox`, `POST /inbox/threads`, `POST /inbox/threads/{id}/messages`, `POST /inbox/threads/{id}/complete`
- `GET /portal/me`, `GET /portal/appointments`, `GET /portal/results`, `GET /portal/messages`
- `GET /admin/audit`, `GET /analytics/overview`; future read-only `/fhir/*`.

所有 API 返回统一的 `resource id`，日期 ISO8601；分页标准统一；请求校验后返回 400/403/404/409/422；敏感字段禁止直接在日志中输出。

## 7. 合成演示数据设计

### 7.1 推荐种子规模
- 1 个 Organization、2 个 Departments、12 个 Users（跨角色）、30 个 Patients（全虚构）。
- 60 个 Appointments（历史/今日/未来），40 个 Encounters，20 份 Notes、约 120 条 Observations、70 条 Orders、40 个 Lab Results、10 个 Imaging Reports、20 条 Inbox Threads、10 个模拟账单。
- 至少 3 个完整场景患者：
  - 患者 A：42 岁，慢性病门诊复诊、HbA1c 检验结果、医生回看、患者门户 AVS。
  - 患者 B：急诊病人，从分诊到住院/出院的完整流转。
  - 患者 C：住院患者，有护理生命体征、模拟用药 MAR、转床与出院总结。
- 诊断、药物、检验、病史和姓名全由代码构造为虚构演示信息；不要使用公开训练截图里出现的真实身份信息。

### 7.2 数据一致性要求
- 每条记录必须存在有效 patientId，必需时存在 encounterId；不同患者间记录不得串联。
- Appointment 的日期与 Encounter 的关联要一致；所有状态转换落库；测试数据库可重复 seed/reset。
- 演示数据固定可复现（seed 固定随机种子），适合录屏与自动化测试。

## 8. 开发阶段、优先级和完成标准

| 阶段 | 可交付的真正功能 | 何时算完成 |
|---|---|---|
| Phase 0 | Monorepo、启动说明、DB/schema、Auth/RBAC、Demo Seed、基础布局 | 前后端可启动，能用演示账号登录，审计数据正常 |
| Phase 1 | Patient Search/Register、Schedule、Check-in、Patient Snapshot | 创建患者/预约/签到刷新后不丢失，搜索筛选有效 |
| Phase 2 | Encounter Navigator、Vitals、Problems、Allergies、Medications、Notes | 护士记录可在医生端显示；笔记可保存/签署 |
| Phase 3 | Order Composer、Lab Queue、Results、Inbox、AVS | 跑通 W01 + W02，无假按钮 |
| Phase 4 | Inpatient、Nursing、Flowsheets、MAR、ED、Pharmacy、Radiology | 跨角色状态同步，权限测试通过 |
| Phase 5 | Patient Portal、Billing、Analytics、FHIR-shaped export | 门户只能看自己的数据，报表来自 DB |
| Phase 6 | AI chart summary / drafts / RAG evidence、测试加固、部署演示 | 引用可追踪；未审阅无法自动签署；录屏可演示 |

关键限制：**一次只让 Codex 实现一个小的纵向功能切片**（数据库→API→页面→测试），由人验收后再继续，避免一次性生成 30 个看似完整但无法运行的页面。

## 9. 质量与验收

### 功能真实性
- UI 每个主要 Button 都对应 API/state change 或明确的 disabled + tooltip；不能只有漂亮壳子。
- 页面刷新/重启后数据保持；完整状态历史；任务队列数量准确。
- 角色权限：仅有授权角色可写；patient self-only；跨患者数据查询隔离。

### 代码质量
- 清晰的组件与模块拆分，避免 2000 行巨型页面；API service 层与 UI 分离。
- 提交之前运行 Lint、Typecheck、Unit/Integration/End-to-End tests，报告通过/失败数量。
- 不随意覆盖已有项目，任何 destructive migration、删除文件、云端部署都需要用户确认。

### 安全与合规边界
- 合成数据，不包含真实患者、真实账号信息。
- 保持清晰免责声明；不得宣称 HIPAA 合规、ONC 认证、临床可用，除非独立完成所需评估。
- 启用访问审计、最小权限、输入校验、SQL 参数化、防 XSS/CSRF、错误信息脱敏。
- AI 默认 mock/provider-disabled；真实 LLM 接入前明确数据流、隐私和成本边界。

## 10. 术语与官方/教学参考

1. Epic 软件全览：https://www.epic.com/software/
2. Epic 专科产品：https://www.epic.com/software/specialties/
3. Epic 住院与护理：https://www.epic.com/software/acute-and-inpatient-care/
4. Epic 患者体验/MyChart：https://www.epic.com/software/patient-experience/
5. Epic 预约排班：https://www.epic.com/software/appointment-scheduling/
6. Epic 跨机构互联：https://www.epic.com/software/interoperability/
7. Epic 人群健康：https://www.epic.com/software/population-health/
8. Epic 医疗分析：https://www.epic.com/software/healthcare-intelligence/
9. Epic Art 临床 AI：https://www.epic.com/software/art/
10. open.epic FHIR 技术概述：https://open.epic.com/TechnicalSpecifications
11. UI Health Care Epic 基础培训概览：https://epicsupport.sites.uiowa.edu/epic-resources/hyperspace-epic-basics
12. UI Health Care SmartTools：https://epicsupport.sites.uiowa.edu/epic-resources/smarttools
13. Vanderbilt Epic 公共介绍：https://www.vumc.org/vclic/intro-epic-and-build-capabilities
14. Storyboard 术语定义：https://ehealth.connect-care.ca/epic-systems/epic-modules/storyboard

**此文档是为研发构建的需求规格，不是 Epic 内部机密功能手册，也不是 Epic 官方页面原型或完整商用 EHR 的认证规范。**
