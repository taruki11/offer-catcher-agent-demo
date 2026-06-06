import json, sys, os
sys.path.insert(0, os.path.abspath('.'))
from pathlib import Path

cases = json.loads(Path('eval/golden_cases.json').read_text(encoding='utf-8'))

from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.strategy_planner import gen_strategy_package

for case in cases:
    if case.get('eval_split') != 'stress':
        continue
    print('=== ' + case['case_id'] + ' ===')
    print('  expected_action: ' + str(case.get('expected_action')))
    
    profile = parse_resume(case['resume_text'])
    profile['_city'] = case.get('target_city', '')
    profile['_stage'] = case.get('stage', '')
    profile['_target_role'] = case.get('target_role', '')
    
    print('  has_llm_project: ' + str(profile.get('has_llm_project')))
    print('  has_metrics: ' + str(profile.get('has_metrics')))
    print('  has_rec_project: ' + str(profile.get('has_rec_project')))
    
    scored = rank_jobs(
        resume_text=case['resume_text'],
        profile=profile,
        target_role=case.get('target_role', ''),
        target_city=case.get('target_city', ''),
        stage=case.get('stage', ''),
        top_k=8,
        jobs_path=Path('data/jobs.json')
    )
    
    pkg = gen_strategy_package(scored, profile)
    top3 = pkg.get('priority_top3', [])
    for i, t in enumerate(top3):
        print('  Top' + str(i+1) + ': ' + t['title'] + ' | action=' + t['apply_action'] + ' | pass=' + str(t.get('pass_score')) + ' | risk=' + str(t.get('risk_score')) + ' | growth=' + str(t.get('growth_score')))
    
    actual = top3[0]['apply_action'] if top3 else '?'
    exp = case.get('expected_action', '')
    match_str = 'OK' if actual == exp else 'MISMATCH'
    print('  RESULT: actual=' + actual + ', expected=' + exp + ' => ' + match_str)
    print()
