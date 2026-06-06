"""
诊断脚本：打印每个 stress case 的详细分数和 action 判断轨迹。
用法：python scripts/diag_stress.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.resume_parser import parse_resume
from src.matcher import rank_job_list
from src.strategy_planner import _infer_action


def main():
    golden_path = os.path.join(ROOT, "eval", "golden_cases.json")
    jobs_path = os.path.join(ROOT, "data", "jobs.json")

    with open(golden_path, encoding="utf-8") as f:
        cases = json.load(f)
    with open(jobs_path, encoding="utf-8") as f:
        jobs = json.load(f)

    print("[DIAG] Stress case diagnosis starting...")

    for case in cases:
        if case.get("eval_split") != "stress":
            continue

        profile = parse_resume(case["resume_text"])
        # rank_job_list(resume_text, profile, target_role, target_city, stage, top_k, jobs)
        ranked = rank_job_list(
            case["resume_text"],
            profile,
            case["target_role"],
            case["target_city"],
            case["stage"],
            20,
            jobs,
        )
        top1 = ranked[0] if ranked else {}

        pass_s = top1.get("pass_score", 0)
        risk_s = top1.get("risk_score", 0)
        growth_s = top1.get("growth_score", 0)
        missing = top1.get("missing_skills", [])
        action = _infer_action(top1, profile)
        expected = case.get("expected_action", "?")

        print(f"CASE: {case['case_id']}")
        print(f"  top1 title : {top1.get('title', '?')}")
        print(f"  pass={pass_s}  risk={risk_s}  growth={growth_s}")
        print(f"  missing    : {missing}")
        print(f"  actual     : {action}")
        print(f"  expected   : {expected}")
        print(f"  match?     : {'[PASS]' if action == expected else '[FAIL]'}")
        print()

    print("[DIAG] Diagnosis done.")


if __name__ == "__main__":
    main()
