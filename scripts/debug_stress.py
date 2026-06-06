"""
debug_stress.py — 打印每个 stress case 的详细分数和决策过程
"""
import json, sys
from pathlib import Path

sys.path.insert(0, ".")
from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.conversion import attach_conversion_scores
from src.strategy_planner import gen_strategy_package

cases = json.load(open("eval/golden_cases.json"))
stress_cases = [c for c in cases if c.get("eval_split") == "stress"]

print("=" * 70)
print(f"共 {len(stress_cases)} 个 stress cases")
print("=" * 70)

for c in stress_cases:
    profile = parse_resume(c["resume_text"])
    profile["_city"] = c.get("target_city", "")
    profile["_stage"] = c.get("stage", "")
    profile["_target_role"] = c.get("target_role", "")

    scored = rank_jobs(
        resume_text=c["resume_text"],
        profile=profile,
        target_role=c["target_role"],
        target_city=c["target_city"],
        stage=c["stage"],
        top_k=8,
        jobs_path=Path("data/jobs.json"),
    )
    scored = attach_conversion_scores(scored, profile)
    strategy = gen_strategy_package(scored, profile)
    top3 = strategy.get("priority_top3", [])
    actual = top3[0]["apply_action"] if top3 else "?"
    expected = c.get("expected_action", "?")
    j0 = scored[0] if scored else {}

    pass_s = j0.get("pass_score", "?")
    risk_s = j0.get("risk_score", "?")
    growth_s = j0.get("growth_score", "?")
    missing = j0.get("missing_skills", [])

    print(f"\n{'=' * 70}")
    print(f"Case: {c['case_id']}")
    print(f"  expected_action  = {expected}")
    print(f"  actual_action    = {actual}")
    print(f"  Top1 job        = {j0.get('title', '?')}")
    print(f"  pass_score      = {pass_s}")
    print(f"  risk_score      = {risk_s}")
    print(f"  growth_score    = {growth_s}")
    print(f"  missing_skills  = {missing}")
    print(f"  profile skills  = {profile.get('skills', [])}")
    print(f"  has_metrics     = {profile.get('has_metrics', '?')}")
    print(f"  has_llm_project= {profile.get('has_llm_project', '?')}")

    # 手动走一遍 _infer_action 逻辑
    ps = pass_s if isinstance(pass_s, (int, float)) else 0
    rs = risk_s if isinstance(risk_s, (int, float)) else 100
    gs = growth_s if isinstance(growth_s, (int, float)) else 0
    mc = len(missing) if isinstance(missing, list) else 0

    t_city = profile.get("_city", "")
    t_stage = profile.get("_stage", "")
    j_city = j0.get("city", "")
    j_stage = j0.get("stage", "")

    city_miss = bool(t_city and t_city != "不限" and j_city != t_city)
    stage_miss = bool(t_stage and j_stage != t_stage and j_stage != "不限")

    print(f"  city_match: target={t_city}, job={j_city}, mismatch={city_miss}")
    print(f"  stage_match: target={t_stage}, job={j_stage}, mismatch={stage_miss}")

    # 模拟决策
    if city_miss or stage_miss:
        if ps >= 70 and rs <= 30 and mc <= 2:
            inferred = "冲刺岗位(硬伤但高分)"
        elif ps >= 45 and rs <= 60:
            inferred = "先优化再投(硬伤)"
        else:
            inferred = "暂缓(硬伤)"
    elif ps >= 65 and rs <= 30 and mc <= 2:
        inferred = "立即投递"
    elif mc == 0 and ps >= 60:
        inferred = "立即投递(无缺口)"
    elif ps >= 45 and rs <= 60:
        inferred = "先优化再投"
    elif gs >= 80 and ps >= 50 and rs <= 50:
        inferred = "冲刺岗位"
    else:
        inferred = "暂缓"
    print(f"  inferred_action  = {inferred}")
    if inferred != actual:
        print(f"  ** 不匹配! expected={actual}, inferred={inferred}")

print(f"\n{'=' * 70}")
print("完成")
