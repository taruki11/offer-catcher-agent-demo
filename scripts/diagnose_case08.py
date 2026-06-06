"""diagnose_case08.py — 打印 case_08 的 scores 和 action"""
import sys
sys.path.insert(0, ".")

from pathlib import Path
import json
from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.strategy_planner import gen_strategy_package

cases = json.load(open("eval/golden_cases.json", encoding="utf-8"))
case08 = [c for c in cases if c["case_id"] == "case_08"][0]

profile = parse_resume(case08["resume_text"])
print(f"has_llm={profile['has_llm_project']}, has_rec={profile['has_rec_project']}, has_metrics={profile['has_metrics']}")
print(f"skills: {profile['skills'][:6]}")

ranked = rank_jobs(
    resume_text=case08["resume_text"],
    profile=profile,
    target_role=case08["target_role"],
    target_city=case08["target_city"],
    stage=case08["stage"],
    top_k=8,
    jobs_path=Path("data/jobs.json"),
)

print(f"\nTop5 by priority:")
for j in ranked[:5]:
    print(f"  {j['title']} | pass={j.get('pass_score')} | risk={j.get('risk_score')} | growth={j.get('growth_score')} | pri={j.get('apply_priority')}")

strategy = gen_strategy_package(ranked, profile)
top3 = strategy["priority_top3"]
print(f"\nTop3 actions:")
for t in top3:
    print(f"  {t['title']} -> {t['apply_action']}")
