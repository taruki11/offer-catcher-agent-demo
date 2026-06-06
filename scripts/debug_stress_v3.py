#!/usr/bin/env python3
"""debug_stress_v3.py - 详细打印每个 stress case 的中间状态"""

import json
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，使 import src.xxx 能工作
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.conversion import attach_conversion_scores
from src.strategy_planner import gen_strategy_package, _infer_action

EVAL_PATH = ROOT / "eval" / "golden_cases.json"

def main():
    cases = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    stress_cases = [c for c in cases if c.get("eval_split") == "stress"]

    print(f"Total cases: {len(cases)}")
    print(f"Stress cases: {len(stress_cases)}\n")

    for case in stress_cases:
        cid = case["case_id"]
        print(f"{'='*60}")
        print(f"CASE: {cid}")
        print(f"{'='*60}")

        resume_text = case["resume_text"]
        target_role = case.get("target_role", "")
        target_city = case.get("target_city", "")
        stage = case.get("stage", "")

        # 1. 解析简历
        profile = parse_resume(resume_text)
        profile["_city"] = target_city
        profile["_stage"] = stage
        profile["_target_role"] = target_role

        print(f"\n[PROFILE]")
        print(f"  _target_role: {profile.get('_target_role')}")
        print(f"  _city: {profile.get('_city')}")
        print(f"  _stage: {profile.get('_stage')}")
        print(f"  has_llm_project: {profile.get('has_llm_project')}")
        print(f"  has_metrics: {profile.get('has_metrics')}")
        print(f"  has_rec_project: {profile.get('has_rec_project')}")
        print(f"  skills count: {len(profile.get('skills', []))}")
        print(f"  skills (first 10): {profile.get('skills', [])[:10]}")

        # 2. 计算 match + conversion 分数
        scored = rank_jobs(
            resume_text=resume_text,
            profile=profile,
            target_role=target_role,
            target_city=target_city,
            stage=stage,
            top_k=8,
            jobs_path=ROOT / "data" / "jobs.json",
        )

        # 3. 打印 top3 的详细分数
        pkg = gen_strategy_package(scored, profile)
        top3 = pkg.get("priority_top3", [])

        print(f"\n[TOP3 JOBS]")
        for i, t in enumerate(top3):
            print(f"  Top{i+1}: {t['title']}")
            print(f"    direction: {t.get('direction')}")
            print(f"    pass_score: {t.get('pass_score')}")
            print(f"    risk_score: {t.get('risk_score')}")
            print(f"    growth_score: {t.get('growth_score')}")
            print(f"    match_score: {t.get('match_score')}")
            print(f"    apply_priority: {t.get('apply_priority')}")
            print(f"    missing_skills: {t.get('missing_skills')}")
            print(f"    apply_action: {t.get('apply_action')}")

        # 4. 对比 expected_action
        if top3:
            actual_action = top3[0]["apply_action"]
            expected_action = case.get("expected_action", "")
            match = "OK" if actual_action == expected_action else "MISMATCH"
            print(f"\n[ACTION COMPARE]")
            print(f"  expected: {expected_action}")
            print(f"  actual:   {actual_action}")
            print(f"  result:   {match}")

            # 5. 打印 _infer_action 的决策依据
            print(f"\n[DECISION DETAIL] (top1 job)")
            job = top3[0]
            pass_s = job.get("pass_score", 50)
            risk_s = job.get("risk_score", 50)
            growth_s = job.get("growth_score", 50)
            missing = job.get("missing_skills", [])
            missing_count = len(missing) if isinstance(missing, list) else 0

            has_llm = bool(profile.get("has_llm_project", False))
            has_met = bool(profile.get("has_metrics", False))
            has_rec = bool(profile.get("has_rec_project", False))
            is_grad = "已毕业" in str(profile.get("_stage", "")) or "2025" in str(profile.get("_stage", ""))

            print(f"  pass={pass_s}, risk={risk_s}, growth={growth_s}")
            print(f"  missing_count={missing_count}")
            print(f"  has_llm={has_llm}, has_metrics={has_met}, has_rec={has_rec}")
            print(f"  is_graduated={is_grad}")
            print(f"  direction_match={profile.get('_target_role') in job.get('direction', '') or job.get('direction', '') in profile.get('_target_role', '')}")

        print()

if __name__ == "__main__":
    main()
