import json, sys, os
sys.path.insert(0, os.path.abspath('.'))
from pathlib import Path

cases = json.loads(Path('eval/golden_cases.json').read_text(encoding='utf-8'))

from src.conversion import attach_conversion_scores, calc_pass_score, calc_risk_score, calc_growth_score

for case in cases:
    if case.get('eval_split') != 'stress':
        continue
    from src.resume_parser import parse_resume
    profile = parse_resume(case['resume_text'])
    profile['_city'] = case.get('target_city', '')
    profile['_stage'] = case.get('stage', '')
    profile['_target_role'] = case.get('target_role', '')
    
    # 用第一个岗位测试分数计算
    from src.matcher import load_jobs
    jobs = load_jobs(Path('data/jobs.json'))
    if not jobs:
        continue
    job = jobs[0]
    
    ps = calc_pass_score(profile, job, case['resume_text'])
    rs = calc_risk_score(profile, job, case['resume_text'])
    gs = calc_growth_score(profile, job)
    
    print(case['case_id'] + ': pass=' + str(ps) + ' risk=' + str(rs) + ' growth=' + str(gs))
    print('  has_llm=' + str(profile.get('has_llm_project')) + ' has_metrics=' + str(profile.get('has_metrics')) + ' has_rec=' + str(profile.get('has_rec_project')))
    print()
