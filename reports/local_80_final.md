# Offer 捕手本地 80 分冲刺验收

Generated: 2026-06-05

## 修改文件

- `src/strategy_planner.py`
  - 重写投递动作判定阈值。
  - 收紧“立即投递”条件，避免 pass 中等且 missing skill 较多时过度乐观。
  - 对城市/阶段错位的强候选输出“冲刺岗位”，更符合真实投递策略。
  - 修复 Top3 策略组合中“立即投递”和“暂缓”同时出现的冲突。

- `src/matcher.py`
  - 增加迁移型强匹配补偿：当岗位方向不完全一致，但技能匹配和项目匹配都很高时，给予少量 match_score 加分。
  - 修复 CV 强匹配岗位被泛平台岗位抢占 Match Top1 的问题。

## Baseline

WorkBuddy 上一轮改动后，本地真实状态为：

| Split | PASS | Match Top1 | Priority Top1 | Action Acc | Error |
|---|---:|---:|---:|---:|---|
| core | 5/8 | 100% | 100% | 75.0% | E9_ACTION_MISMATCH, E9_STRATEGY_CONFLICT |
| stress | 4/7 | 85.7% | 100% | 57.1% | E9_ACTION_MISMATCH, E5_MATCH_RANK_MISORDER |

## Final

| Split | PASS | Match Top1 | Priority Top1 | Action Acc | Recall@5 |
|---|---:|---:|---:|---:|---:|
| core | 8/8 | 100% | 100% | 100% | 100% |
| stress | 7/7 | 100% | 100% | 100% | 100% |

## 已通过测试

- `python -m py_compile app.py src/*.py scripts/run_eval.py ...`
- `python scripts/run_eval.py --split core`
- `python scripts/run_eval.py --split stress`
- `python scripts/test_jd_intake.py`
- `python scripts/test_llm_fallback.py`
- `python scripts/test_evidence.py`
- `python scripts/test_data_ingestion.py`
- `python scripts/check_deploy_ready.py`

## 当前评分判断

本地版本已达到 80 分以上标准。核心理由：

- 核心与压力 golden cases 全部通过。
- JD Intake、LLM fallback、证据链、公开岗位导入均通过。
- 不依赖真实 API key，默认 fallback 可运行。
- 仍需 3060 恢复后做远程同步和健康检查。

## 明天 3060 恢复后执行

```powershell
scp -r app.py check_health.ps1 requirements.txt .env.example README.md data docs prompts src eval scripts reports 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/
ssh 3060 "powershell -NoProfile -ExecutionPolicy Bypass -File D:\Pycharm_workplace\offer_catcher_agent_demo_20260602\scripts\verify_3060.ps1"
```

