"""
scripts/test_jd_intake.py — JD Intake + rank_job_list 集成测试
验证：粘贴 JD 文本 → parse_jd → normalize → rank_job_list 全链路
"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.jd_parser import parse_jd
from src.job_intake import parse_single_jd, parse_multiple_jds, normalize_job, merge_builtin_and_user_jobs, load_builtin_jobs
from src.resume_parser import parse_resume
from src.matcher import rank_job_list

JD_LLM = """岗位：大模型应用算法实习生
公司：字节跳动 AI 部门
地点：北京
方向：大模型应用算法
要求：熟悉 Python、PyTorch、Transformer，有 RAG/Agent 项目经验，了解 LangChain 和向量数据库。负责企业级 LLM 应用开发和 Agent 工作流设计。面试覆盖 RAG 召回策略、Agent 兜底、Prompt 工程。"""

JD_REC = """岗位：推荐算法实习生
公司：快手
地点：深圳
方向：推荐算法
要求：熟悉推荐系统、召回排序，掌握 Python 和深度学习框架。了解 A/B Test 和离线评估指标。负责内容推荐模型优化和线上 A/B 实验。"""

RESUME = """张同学 | 计算机科学与技术 | 2026 届硕士
技能：Python、PyTorch、Transformer、RAG、Agent、Embedding
项目：RAG 知识库问答系统、LLM Agent 工具调用 Demo"""


def main():
    print("=== Test 1: parse_single_jd ===")
    j1 = parse_single_jd(JD_LLM)
    assert j1["title"], "title missing"
    assert j1["skills"], "skills missing"
    assert j1["source"] == "user_pasted", f"source={j1['source']}"
    print(f"  [OK] title={j1['title']}, skills={j1['skills'][:5]}, source={j1['source']}")

    print("=== Test 2: parse_multiple_jds ===")
    multi = f"{JD_LLM}\n---JD---\n{JD_REC}"
    jobs = parse_multiple_jds(multi)
    assert len(jobs) == 2, f"expected 2, got {len(jobs)}"
    print(f"  [OK] parsed {len(jobs)} JDs: {[j['title'] for j in jobs]}")

    print("=== Test 3: normalize + merge ===")
    import pathlib as _pl
    _ROOT = _pl.Path(__file__).parent.parent
    builtin = load_builtin_jobs(str(_ROOT / "data" / "jobs.json"))
    merged = merge_builtin_and_user_jobs(builtin, jobs)
    print(f"  [OK] builtin={len(builtin)}, user={len(jobs)}, merged={len(merged)}")

    print("=== Test 4: rank_job_list (LLM JD) ===")
    profile = parse_resume(RESUME)
    scored = rank_job_list(RESUME, profile, "大模型应用算法", "北京", "实习", 5, [j1])
    assert len(scored) > 0, "rank_job_list returned empty"
    top = scored[0]
    print(f"  [OK] Top1={top['title']}, match={top.get('match_score')}, apply_priority={top.get('apply_priority')}")

    print("=== Test 5: golden cases with jd_text ===")
    golden_path = pathlib.Path("eval/golden_cases.json")
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    jd_cases = [c for c in golden if "jd_text" in c]
    print(f"  [OK] Found {len(jd_cases)} JD intake golden cases: {[c['case_id'] for c in jd_cases]}")

    for case in jd_cases:
        job = parse_single_jd(case["jd_text"])
        profile = parse_resume(case["resume_text"])
        scored = rank_job_list(case["resume_text"], profile, case["target_role"],
                               case["target_city"], case["stage"], 3, [job])
        assert scored, f"rank_job_list empty for {case['case_id']}"
        print(f"  [OK] {case['case_id']}: top match={scored[0].get('match_score')}, apply={scored[0].get('apply_priority')}")

    print("\n=== All JD Intake tests passed ===")


if __name__ == "__main__":
    main()
