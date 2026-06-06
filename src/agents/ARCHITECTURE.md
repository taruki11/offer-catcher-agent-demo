# Agent 架构文件结构

```
src/
├── agent_state.py          ← 共享 State (dataclass)
├── agents/
│   ├── __init__.py
│   ├── career_intent_agent.py       ← Agent 1: 方向推断
│   ├── job_scout_agent.py           ← Agent 2: 岗位搜索
│   ├── jd_analyst_agent.py          ← Agent 3: JD 分析
│   ├── resume_evidence_agent.py     ← Agent 4: 简历证据
│   ├── match_reasoning_agent.py     ← Agent 5: 匹配推理
│   ├── counterfactual_planning_agent.py ← Agent 6: 反事实模拟
│   ├── resume_coach_agent.py        ← Agent 7: 简历优化
│   ├── interview_coach_agent.py     ← Agent 8: 面试准备
│   └── strategy_planner_agent.py    ← Agent 9: 投递策略
└── langgraph_workflow.py   ← 编排流水线
```

## 验证结果

- py_compile: 13 files ✅ ALL PASS
- 离线 Demo: 9 Agent 全部执行成功
  - 方向推断: Agent算法/校招
  - 岗位匹配: 8/8
  - 策略输出: 稳投=3 冲刺=3

## 每个 Agent 的设计

| Agent | LLM prompt | Fallback | 输出 |
|---|---|---|---|
| CareerIntent | 技术猎头判断方向 | 关键词规则 | direction/stage/cities/risk |
| JobScout | 联网搜索+本地 | 本地corpus过滤 | JDProfile list |
| JDAnalyst | 阅读JD抽取画像 | 关键词提取 | skills/education/hidden |
| ResumeEvidence | 严格证据提取 | 关键词检测 | skill/project/gap evidence |
| MatchReasoning | 面试官式匹配 | 技能交集计算 | match_score/reasoning/missing |
| Counterfactual | 量化补强模拟 | gap映射 | what-if items/top3 payoffs |
| ResumeCoach | 证据约束改写 | 简单建议 | can_rewrite/need_project |
| InterviewCoach | 面试准备包 | 泛化问题 | questions/7day plan |
| StrategyPlanner | 投递策略分类 | 阈值分类 | safe/stretch/skip jobs |
