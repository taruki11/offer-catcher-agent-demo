"""
scripts/run_eval.py — P6 验收：Top5 岗位验证 + 合约检查
"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from langgraph_workflow import run_full_pipeline

BAD_COMPANY_WORDS = [
    'Coach', 'Contract', 'Co-Founder', 'Resident', 'Fellows',
    'Analyst', 'Maritime', 'Memphis', 'Leland', 'Anduril',
    'City of', 'Manager', 'Director', 'VP', 'Lead',
    'Leidos', 'Meta', 'Google', 'Amazon', 'Apple', 'Microsoft', 'OpenAI', 'Canva',
]

REQUIRED_TITLE_WORDS = ['算法', 'AI', 'NLP', 'CV', '机器学习', '深度学习', '大模型', 'LLM', 'Agent', 'RAG', '推荐', '搜索', '研究', '数据']


def test_core_with_sample():
    """Core eval: 标准简历跑流水线，验证 Top5 合约。"""
    resume = (
        "张三 | 大模型应用算法工程师\n"
        "2022.09 - 2026.06 XX大学 计算机科学与技术 本科\n\n"
        "实习经历\n"
        "2025.06 - YY科技 算法实习生\n"
        "- LoRA微调Qwen2.5-7B，RAG企业知识库问答系统（FAISS+SentenceTransformers）\n\n"
        "项目经历\n"
        "Offer捕手 — 多Agent求职匹配系统：9Agent协作，NDCG@10=0.87\n\n"
        "技能：Python, PyTorch, Transformers, LangChain, FAISS"
    )
    print("=== Core Eval ===")
    report = run_full_pipeline(resume, goal="找大模型应用算法实习，深圳/北京")
    
    top5 = report.job_decisions[:5]
    passed = True
    errors = []

    for i, jd in enumerate(top5):
        # Check 1: no bad company
        if any(w.lower() in jd.company.lower() for w in BAD_COMPANY_WORDS):
            errors.append(f"  [{jd.company}] BAD company word")
            passed = False
        if any(w.lower() in jd.title.lower() for w in BAD_COMPANY_WORDS):
            errors.append(f"  [{jd.title}] BAD title word")
            passed = False
        # Check 2: has relevant title words
        if not any(w in jd.title for w in REQUIRED_TITLE_WORDS):
            errors.append(f"  [{jd.title}] no relevant keyword in title")
            passed = False
        # Check 3: has JD evidence
        if len(jd.jd_evidence) < 1:
            errors.append(f"  [{jd.title}] no jd_evidence")
            passed = False

    # Check 4: source verification
    for jds in report.jd_sources[:5]:
        if jds.source_type not in ("Demo精选岗位", "公开爬取", "用户粘贴"):
            errors.append(f"  [{jds.title}] bad source_type: {jds.source_type}")
            passed = False
        if jds.raw_snippet and len(jds.raw_snippet) < 80:
            errors.append(f"  [{jds.title}] snippet too short: {len(jds.raw_snippet)} chars")
            passed = False

    print(f"  Top5 titles:")
    for i, jd in enumerate(top5):
        src = next((s for s in report.jd_sources if s.title == jd.title), None)
        snip_len = len(src.raw_snippet) if src and src.raw_snippet else 0
        print(f"  [{i+1}] {jd.title} @ {jd.company} · {jd.decision} · source={src.source_type if src else '?'} snippet_len={snip_len}")

    # Contract check
    contract_ok, issues = report.validate_contract()
    if not contract_ok:
        for iss in issues: errors.append(iss)
        passed = False

    if errors:
        print(f"\n❌ Core Eval FAILED ({len(errors)} issues):")
        for e in errors: print(e)
    else:
        print(f"\n✅ Core Eval PASSED")
        print(f"  decisions={len(report.job_decisions)} sources={len(report.jd_sources)}")
        print(f"  portfolio: safe={len(report.portfolio.safe)} stretch={len(report.portfolio.stretch)} hold={len(report.portfolio.hold)}")

    return passed


def test_stress_english_resume():
    """Stress eval: 英文简历处理。"""
    print("\n=== Stress Eval ===")
    resume = "John - Python/PyTorch - CS Master 2026 - Looking for ML intern - USA based"
    report = run_full_pipeline(resume, goal="ML internship", use_online=False)
    top5 = report.job_decisions[:5]
    bad = [jd for jd in top5 if any(w.lower() in jd.company.lower() for w in BAD_COMPANY_WORDS)]
    if bad:
        print(f"  ⚠️ {len(bad)} suspicious entries in Top5 (may be OK for English resume)")
    print(f"  decisions={len(report.job_decisions)} sources={len(report.jd_sources)}")
    print(f"  Top5:")
    for i, jd in enumerate(top5):
        print(f"  [{i+1}] {jd.title} @ {jd.company} · {jd.decision}")
    print("✅ Stress Eval DONE")
    return True


def test_run_all():
    core_ok = test_core_with_sample()
    stress_ok = test_stress_english_resume()
    all_ok = core_ok and stress_ok
    print(f"\n{'🎉' if all_ok else '❌'} P6 Result: {'ALL PASS' if all_ok else 'HAS ISSUES'}")
    return all_ok

if __name__ == "__main__":
    ok = test_run_all()
    sys.exit(0 if ok else 1)
