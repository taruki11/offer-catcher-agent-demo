# Baseline Report — 本地 80 分目标

Generated: 2026-06-05 00:40

---

## Core Eval

| Metric | Value | Target |
|---|---|---|
| PASS_CASES | 6/8 | >= 7/8 |
| PASS_RATE | 75.0% | >= 87.5% |
| MATCH_TOP1_ACC | 85.7% | >= 85.7% |
| PRIORITY_TOP1_ACC | 85.7% | >= 85.7% |
| ACTION_ACC | 87.5% | >= 87.5% |
| MATCH_RECALL_AT_5 | 100% | = 100% |
| PRIORITY_RECALL_AT_5 | 100% | = 100% |

Errors: E5_MATCH_RANK_MISORDER:1, E5_PRIORITY_RANK_MISORDER:1, E9_ACTION_MISMATCH:1

Agent-level: ApplicationRanker:2, StrategyPlanner:1

---

## Stress Eval

| Metric | Value | Target |
|---|---|---|
| PASS_CASES | 3/7 | >= 5/7 |
| PASS_RATE | 42.9% | >= 71.4% |
| MATCH_TOP1_ACC | 100% | 不下降 |
| PRIORITY_TOP1_ACC | 85.7% | >= 85.7% |
| ACTION_ACC | 57.1% | >= 71.4% |
| MATCH_RECALL_AT_5 | 100% | = 100% |
| PRIORITY_RECALL_AT_5 | 100% | = 100% |

Errors: E9_ACTION_MISMATCH:3, E5_PRIORITY_RANK_MISORDER:1, E9_STRATEGY_CONFLICT:1

Agent-level: StrategyPlanner:4, ApplicationRanker:1

---

## 失败 Case 详情

### case_05 (core, E5_MATCH + E5_PRIORITY)
- target_role: 大模型应用算法
- target_city: 成都
- Match Top1: 大模型 Agent 应用实习生 (expected: 大模型应用算法实习生)
- Priority Top1: 大模型 Agent 应用实习生 (expected: 大模型应用算法实习生)
- Action: 冲刺岗位 (expected: 冲刺岗位) -- action 正确
- Root cause: matcher.py title 精确匹配加分不足，Agent 岗位排名高于算法岗位

### case_08 (core, E9_ACTION_MISMATCH)
- target_role: 大模型应用算法
- target_city: 广州
- Match Top1: 计算机视觉算法实习生（检测方向）(expected: [])
- Action: 先优化再投 (expected: 暂缓)
- profile: CV 背景，无 LLM 项目，has_metrics=True
- Root cause: StrategyPlanner 对 CV→LLM 转移判断过度乐观，应判"暂缓"

### Stress 失败 Case（待 run_eval.py --split stress 详细输出）
- E9_ACTION_MISMATCH: 3 个
- E5_PRIORITY_RANK_MISORDER: 1 个
- E9_STRATEGY_CONFLICT: 1 个
- 需进一步诊断具体 case_id

---

## 其他测试

| Test | Result |
|---|---|
| py_compile (app.py, src/*.py, scripts/*.py) | PASS |
| test_data_ingestion.py | PASS |
| test_jd_intake.py | PASS |
| test_llm_fallback.py | PASS |
| test_evidence.py | PASS |
| check_deploy_ready.py | PASS |

---

## 数据文件

| File | Count |
|---|---|
| data/jobs.json | 20 |
| data/public_jobs_sample.json | 30 |
| data/jobs_merged.json | 48 |
| eval/golden_cases.json | 17 |

---

## 下一步

1. 读取 src/strategy_planner.py, src/conversion.py, src/matcher.py, src/evaluator.py
2. 诊断 case_05 (matcher title 匹配) 和 case_08 (strategy_planner CV→LLM)
3. 诊断 stress eval 3 个 E9_ACTION_MISMATCH
4. 修复 matcher.py title_exact_match 破 tie 逻辑
5. 修复 strategy_planner.py 投递动作判断
6. 修复 conversion.py pass/risk/growth 分数计算
