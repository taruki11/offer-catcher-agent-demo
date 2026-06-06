# WorkBuddy 提示词：Offer 捕手商业化差异化版本

请接手「Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统」，但要注意：这个项目不能再做成一个重 RAG 项目。

用户已经有一个很完整的 RAG/Agent 项目：

```text
D:\Pycharm_workplace\llm_for_rec_agent
```

该项目已经覆盖：

- 推荐系统技术问答 RAG-Agent
- BM25 + dense hybrid retrieval
- RRF / reranker 评估
- LoRA SFT / DPO ablation
- citation audit / hallucination audit
- Agent routing benchmark
- Qwen 1.5B / 3B / 7B 对比

所以 Offer 捕手如果继续强调“RAG + Agent + 检索问答”，会和已有项目高度重复，而且会显得是已有项目的简化版。

## 一、Offer 捕手的新定位

请把 Offer 捕手改成一个更偏业务、更能商业化、更能体现求职真实价值的项目：

```text
Offer 捕手：面向学生的求职转化率优化与岗位投递决策系统
```

或者：

```text
Offer 捕手：基于 LLM Agent 的校招投递决策与简历转化率优化平台
```

核心一句话：

> Offer 捕手不是知识库问答系统，而是把学生求职流程建模为“岗位机会发现 → 投递优先级决策 → 简历版本优化 → 初筛通过率提升 → 面试准备”的商业闭环，目标是提升学生从“看到岗位”到“获得面试”的转化率。

## 二、和 llm_for_rec_agent 的差异

请在设计和汇报中明确区分：

| 维度 | llm_for_rec_agent | Offer 捕手 |
|---|---|---|
| 核心问题 | 推荐系统知识问答、RAG 准确性 | 学生求职决策、投递转化率 |
| 技术主线 | RAG、SFT、DPO、citation audit | 人岗匹配、投递排序、简历转化率优化 |
| 用户 | 学习推荐系统/LLM 的技术用户 | 正在求职的学生、校招候选人 |
| 结果 | 回答问题是否有引用、是否幻觉 | 投哪个岗位、怎么改简历、如何提升初筛 |
| 评估指标 | Recall、MRR、citation coverage | MatchScore、PassScore、ApplyPriority、GapClosure |
| 商业价值 | 技术学习助手 | 求职服务、校招运营、职业中心工具 |

RAG 在 Offer 捕手里只能是底层辅助能力，不要当主角。可以用于：

- 召回岗位 JD
- 补充岗位能力要求
- 检索面试经验

但项目主线必须是：

```text
求职转化率优化 + 投递决策 + 简历版本管理
```

## 三、Demo 应该做成什么样

请不要只做“简历匹配 JD”的聊天页面。Demo 应该更像一个求职决策驾驶舱。

建议页面模块：

1. 学生画像区
   - 简历文本 / PDF
   - 目标方向
   - 城市
   - 求职阶段
   - 风险偏好：稳妥投递 / 平衡 / 冲刺

2. 岗位机会漏斗
   - 岗位池总数
   - 召回岗位数
   - 高匹配岗位数
   - 建议优先投递数
   - 冲刺岗位数

3. 投递优先级榜单
   每个岗位不要只给 MatchScore，还要给：
   - MatchScore：岗位匹配度
   - PassScore：简历初筛通过概率估计
   - GrowthScore：成长/冲刺价值
   - RiskScore：短板风险
   - ApplyPriority：最终投递优先级

4. 简历版本优化
   - 通用简历版本
   - 针对大模型应用算法岗位的版本
   - 针对推荐算法岗位的版本
   - 针对 AI 平台/后端岗位的版本
   - 每个版本给出关键词覆盖率和建议改写

5. 投递策略建议
   - 今天优先投哪 3 个岗位
   - 哪些岗位适合冲刺
   - 哪些岗位需要先补简历再投
   - 7 天投递计划

6. 面试准备
   - 不是泛泛生成面试题，而是基于目标岗位和简历短板生成追问
   - 标注哪些问题是“高概率被追问”

## 四、新算法表达

不要只写 RAG 召回公式。请把算法表达升级为“投递转化率建模”。

候选岗位召回：

```text
CandidateJobs = Retrieve(Profile, JobPool, Preference)
```

岗位匹配分：

```text
MatchScore = 0.30*S_skill
           + 0.25*S_project
           + 0.20*S_experience
           + 0.15*S_direction
           + 0.10*S_growth
```

初筛通过分：

```text
PassScore = 0.40*K_keyword
          + 0.25*E_evidence
          + 0.20*M_metric
          + 0.15*R_readability
```

投递优先级：

```text
ApplyPriority = 0.45*MatchScore
              + 0.35*PassScore
              + 0.15*GrowthScore
              - 0.20*RiskScore
```

这里的含义：

- `K_keyword`：JD 关键词覆盖率
- `E_evidence`：简历中是否有项目证据支撑
- `M_metric`：是否有 NDCG、HitRate、A/B Test、延迟、准确率等量化指标
- `R_readability`：简历表达是否清楚、是否 ATS 友好
- `RiskScore`：岗位硬要求缺口、城市不匹配、经验不足等风险

这样 Offer 捕手就不是 RAG 项目，而是“求职投递决策系统”。

## 五、Agent 也要改名，变得更业务

不要只叫 Parser / Retriever / RAG Agent。建议改成：

1. Profile Builder Agent
   - 构建学生求职画像

2. Opportunity Scout Agent
   - 从岗位池里发现机会

3. Application Ranker Agent
   - 计算 MatchScore、PassScore、ApplyPriority

4. Resume Conversion Agent
   - 生成不同岗位方向的简历优化版本

5. Interview Readiness Agent
   - 生成面试追问和准备计划

6. Strategy Planner Agent
   - 生成 7 天投递策略和冲刺/稳妥组合

## 六、商业化故事

汇报时可以讲三种商业落地方向：

1. 学生端 ToC
   - 求职助手
   - 简历优化报告
   - 面试准备包
   - 高级功能按次或会员制

2. 高校/训练营 ToB2C
   - 给职业发展中心或训练营使用
   - 批量诊断学生简历
   - 输出就业准备度和岗位推荐

3. 企业校招 ToB
   - 帮企业提前识别候选人和岗位适配度
   - 优化校招触达
   - 对学生进行岗位推荐和候选人 nurturing

当前参赛 Demo 以学生端为主，但汇报里可以提到高校/企业场景，体现落地可行性。

## 七、当前代码改造建议

现有项目目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

当前已有：

- `app.py`
- `data/jobs.json`
- `src/resume_parser.py`
- `src/matcher.py`
- `src/llm_client.py`
- `prompts/`
- 静态网页 MVP

请在现有结构上改，不要推翻。

建议新增/修改：

```text
src/conversion.py          计算 PassScore、KeywordCoverage、RiskScore
src/strategy_planner.py    生成 7 天投递策略
src/report_generator.py    生成 Markdown 求职策略报告
data/resume_templates.json 简历改写模板
```

`app.py` 页面要从“匹配 Demo”升级为“求职决策驾驶舱”。

## 八、验收标准

完成后请确保：

- Demo 能在 3060 远程运行
- 页面展示的不只是岗位匹配，而是投递策略
- 每个岗位至少有 MatchScore、PassScore、RiskScore、ApplyPriority
- 能生成 7 天投递计划
- 能导出 Markdown 求职策略报告
- 汇报材料明确说明：Offer 捕手不是另一个 RAG 项目，而是求职转化率优化系统
- 项目完成后同步回本地留档目录

请先检查当前远程 D 盘项目状态，然后在现有 MVP 上做业务化改造。
