# WorkBuddy 提示词：Offer 捕手 Top50 多 Agent 深度版

请接手继续开发「Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统」。

这次请特别注意：用户不是只想做一个普通网页、语义匹配工具、RAG 问答工具或简历优化小助手。用户的真实目标有两个：

1. **比赛目标**：腾讯青科实训营作业一冲前 50，争取直通复试机会。
2. **求职目标**：沉淀成一个能写进简历、能面试深挖、能体现大模型应用算法 / Agent 应用算法能力的纵深项目。

所以这个项目必须做成一个“多 Agent 求职决策系统”，而不是只做“简历和 JD 语义匹配”。

## 一、最新项目定位

项目名：

```text
Offer 捕手：基于多 Agent 协作的学生岗位匹配与简历转化率优化系统
```

核心一句话：

> Offer 捕手将学生求职过程拆解为画像构建、机会发现、岗位精排、差距诊断、简历改写、投递策略和面试准备等多个可协作 Agent，通过结构化中间状态和可解释决策链，帮助学生提升岗位匹配效率和简历初筛命中率。

请注意：**RAG/语义召回只是底层能力，不是项目主角。项目主角是多 Agent 怎么协作、怎么分工、怎么形成决策闭环。**

## 二、为什么不能只做语义匹配

语义匹配本身不够高级，评委也容易觉得只是 embedding similarity + LLM 总结。Offer 捕手要高级，必须体现：

- 多 Agent 任务拆解
- Agent 之间的结构化状态传递
- 不同 Agent 的角色边界
- 诊断、改写、投递策略之间的闭环
- 可解释的决策链路
- 面向真实学生求职的完整工作流

最终展示给评委的不是“系统算出相似度”，而是：

```text
我如何从一个学生简历出发，经过多个 Agent 的协作，生成一套可执行的求职作战方案。
```

## 三、建议的 Agent 架构

请把 Demo 明确设计成 7 个 Agent 的协同工作流：

### 1. Profile Builder Agent

输入：简历文本 / PDF、求职偏好。

输出：学生画像。

字段包括：

- education：教育背景
- skills：技能栈
- projects：项目经历
- metrics：量化指标
- target_roles：目标岗位
- strength_tags：优势标签
- weak_tags：风险标签

### 2. JD Intelligence Agent

输入：岗位库 JD。

输出：岗位画像。

字段包括：

- required_skills
- bonus_skills
- business_domain
- screening_keywords
- interview_topics
- hard_requirements

### 3. Opportunity Scout Agent

输入：学生画像、岗位画像、偏好。

作用：从岗位池中发现机会，输出候选岗位池。

注意：这里可以用 embedding / TF-IDF / keyword recall，但不要把它讲成唯一核心。

### 4. Application Ranker Agent

输入：候选岗位池、学生画像。

输出：

- MatchScore：岗位匹配度
- PassScore：简历初筛通过潜力
- RiskScore：投递风险
- GrowthScore：成长/冲刺价值
- ApplyPriority：投递优先级

建议公式：

```text
ApplyPriority = 0.40*MatchScore
              + 0.30*PassScore
              + 0.15*GrowthScore
              - 0.15*RiskScore
```

### 5. Gap Diagnosis Agent

输入：目标岗位 + 学生画像。

输出：

- 缺失技能
- 表达风险
- 项目证据不足
- 关键词覆盖不足
- 面试高风险追问点

### 6. Resume Conversion Agent

输入：差距诊断结果、目标岗位。

输出：

- 原句
- 问题
- 建议改写
- 为什么这样改
- 对应提升的 JD 关键词

注意：这个 Agent 是项目亮点之一，因为它直接影响“初筛命中率”。

### 7. Strategy Planner Agent

输入：岗位排序、风险、简历优化结果。

输出：

- 今日优先投递 Top3
- 稳妥 / 平衡 / 冲刺岗位组合
- 7 天投递计划
- 7 天面试准备计划
- 哪些岗位要先改简历再投

## 四、Agent 协作界面怎么设计

Demo 页面不要只是聊天窗口。请做成“Agent 决策驾驶舱”。

建议页面结构：

### 顶部：项目任务流

横向展示 7 个 Agent 节点：

```text
Profile Builder → JD Intelligence → Opportunity Scout → Application Ranker → Gap Diagnosis → Resume Conversion → Strategy Planner
```

每个节点显示：

- 输入
- 输出
- 状态：已完成 / 处理中 / 待执行
- 当前关键发现

### 左侧：学生输入区

- 简历上传 / 粘贴
- 目标方向
- 目标城市
- 求职阶段
- 风险偏好：稳妥 / 平衡 / 冲刺

### 中间：岗位投递优先级榜单

每个岗位卡片显示：

- MatchScore
- PassScore
- RiskScore
- GrowthScore
- ApplyPriority
- 推荐动作：立即投递 / 先优化再投 / 冲刺岗位 / 暂缓

### 右侧：Agent 诊断详情

点击岗位后展示：

- 多维雷达图
- Agent 推理链摘要
- 能力缺口
- 简历改写建议
- 高频面试追问

### 底部：投递策略报告

- 一键导出 Markdown
- 包含岗位排序、简历优化、7 天策略、面试准备

## 五、比赛前 50 的评分对应策略

评分维度包括：思辨深度、创意巧思、功能完整度、交互体验、落地可行性。

请按下面方向做：

### 1. 思辨深度

不要只说“学生找岗位难”，要说：

> 学生求职不是单点问答问题，而是一个多阶段决策问题：岗位机会发现、匹配排序、简历转化率优化、投递优先级规划和面试准备互相影响。

### 2. 创意巧思

亮点是：

> 用多 Agent 协作模拟一个求职顾问团队，而不是让一个大模型一次性回答所有问题。

### 3. 功能完整度

必须至少有：

- 简历输入
- 岗位推荐
- 匹配评分
- 风险诊断
- 简历改写
- 投递策略
- 面试准备
- 报告导出

### 4. 交互体验

必须让评委一眼看到“高级”：

- Agent 流程条
- 岗位卡片
- 多维雷达图
- 简历改写对照
- 7 天策略计划
- 可导出报告

### 5. 落地可行性

强调：

- 学生真实需要
- 不依赖大规模数据
- 小型岗位库即可演示
- 后续可接入校招官网、学校就业平台、企业 ATS

## 六、和用户已有 RAG 项目的差异

用户已有 `llm_for_rec_agent`，它是重 RAG / 推荐系统知识问答 / 检索评估 / SFT-DPO 项目。

Offer 捕手必须避免重复：

- 不要主打 citation RAG
- 不要主打知识库问答
- 不要主打模型微调
- 不要主打检索 benchmark

Offer 捕手要主打：

- 多 Agent 工作流
- 求职投递决策
- 简历转化率优化
- 人岗匹配排序
- Agent 间状态协作
- 真实业务闭环

一句话区分：

> llm_for_rec_agent 证明用户会做 RAG/Agent 技术系统；Offer 捕手证明用户能把 Agent 技术做成真实业务决策产品。

## 七、当前项目状态

项目目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

远程运行源：3060 机器同路径。

本地只用于留档，不默认运行。

当前已有：

```text
app.py
requirements.txt
.env.example
data/jobs.json
src/resume_parser.py
src/matcher.py
src/llm_client.py
prompts/
index.html
styles.css
src/app.js
docs/方案说明.md
docs/演示脚本.md
```

已验证：

- Streamlit MVP 可以在 3060 启动
- 规则版 TopK 推荐可跑
- 示例简历 Top1 是大模型应用算法实习生

## 八、下一步请实现

请在现有 MVP 上迭代，不要推翻重写。

优先做：

1. 把 `app.py` 改成 Agent 决策驾驶舱。
2. 新增 `src/conversion.py`，计算 PassScore、KeywordCoverage、RiskScore。
3. 新增 `src/strategy_planner.py`，生成 7 天投递策略。
4. 新增 `src/report_generator.py`，导出 Markdown 求职策略报告。
5. 改造 `src/matcher.py`，输出 MatchScore、PassScore、RiskScore、GrowthScore、ApplyPriority。
6. 页面展示 7 个 Agent 的协作流程和每个 Agent 的关键输出。
7. 更新 `docs/方案说明.md`，控制在 1000 字以内。
8. 更新 `docs/演示脚本.md`，做成 3 分钟冲前 50 的演示话术。

## 九、验收标准

完成后请确保：

- 3060 远程能运行 Streamlit Demo
- 示例简历一键运行能完成完整 Agent 流程
- 页面展示 7 个 Agent 的状态和输出
- 岗位榜单包含 MatchScore / PassScore / RiskScore / ApplyPriority
- 至少一个岗位有完整简历改写对照
- 有 7 天投递策略
- 能导出 Markdown 报告
- 汇报材料明确强调多 Agent 协作深度，而不仅仅是语义匹配
- 完成后同步回本地留档

请先检查远程 D 盘目录状态，然后继续实现。
