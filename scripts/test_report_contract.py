"""
test_report_contract.py — FinalDecisionReport 合约验证测试

验证项：
1. 无来源 JD 不允许进入推荐
2. 无简历证据不允许标记 evidence_based=True 的 rewrite
3. 每个 job_decision 至少有 1 条 jd_evidence
4. 每个 resume_action 必须标记 evidence_based 或 need_new_experience
"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from final_report import (
    FinalDecisionReport, JDSource, JobDecision, ResumeAction, Portfolio
)
from langgraph_workflow import run_full_pipeline


def test_no_source_no_recommend():
    """合约 1：无来源 URL 的公开爬取 JD 不能被标记为可验证。"""
    bad_jd = JDSource(
        title="Test Job", company="TestCo", source_type="公开爬取", source_url=""
    )
    assert not bad_jd.is_verifiable(), "公开爬取+无 URL 必须返回 is_verifiable=False"
    good_jd = JDSource(
        title="Test Job", company="TestCo", source_type="公开爬取",
        source_url="https://example.com/jd/123"
    )
    assert good_jd.is_verifiable(), "公开爬取+有 URL 必须返回 is_verifiable=True"

    # 用户粘贴不需要 URL
    user_jd = JDSource(title="Test", company="T", source_type="用户粘贴", source_url="")
    assert user_jd.is_verifiable(), "用户粘贴不需要 URL"

    print("✅ test_no_source_no_recommend PASS")


def test_rewrite_needs_evidence():
    """合约 2：evidence_based=True 的 rewrite 必须要有 original_fragment。"""
    # 有证据的 rewrite
    action_good = ResumeAction(
        action_type="rewrite", target_text="改写成...",
        original_fragment="简历原文：使用了PyTorch", evidence_based=True
    )
    # 无证据的 rewrite 不标记 evidence_based
    action_bad = ResumeAction(
        action_type="rewrite", target_text="改写成...",
        original_fragment="", evidence_based=False
    )
    # evidence_based=True 但没有 original_fragment — 这应该被合约检查抓到
    action_broken = ResumeAction(
        action_type="rewrite", target_text="改写成...",
        original_fragment="", evidence_based=True
    )

    report = FinalDecisionReport(
        job_decisions=[
            JobDecision(
                title="T", company="C", resume_actions=[action_broken],
                jd_evidence=["要求：Python"]
            )
        ]
    )
    issues = report.all_resume_actions_tagged()
    assert len(issues) > 0, "evidence_based=True + 无 original_fragment 应被合约检查抓到"
    print(f"✅ test_rewrite_needs_evidence PASS (caught {len(issues)} issues)")


def test_job_decision_has_jd_evidence():
    """合约 3：每个 job_decision 至少有 1 条 jd_evidence。"""
    jd_good = JobDecision(title="T", company="C", jd_evidence=["要求：Python"])
    jd_bad = JobDecision(title="T2", company="C2", jd_evidence=[])

    assert jd_good.is_valid()
    assert not jd_bad.is_valid()
    print("✅ test_job_decision_has_jd_evidence PASS")


def test_resume_action_tagged():
    """合约 4：每个 resume_action 检查 evidence_based 标记。"""
    actions_ok = [
        ResumeAction(action_type="rewrite", original_fragment="用PyTorch", evidence_based=True),
        ResumeAction(action_type="add_project", evidence_based=False),
    ]
    jd = JobDecision(title="T", company="C", resume_actions=actions_ok, jd_evidence=["要求：Python"])
    report = FinalDecisionReport(job_decisions=[jd])
    passed, issues = report.validate_contract()
    assert passed, f"all tagged actions should pass: {issues}"
    print("✅ test_resume_action_tagged PASS")


def test_full_pipeline_contract():
    """端到端：跑完整流水线，合约必须通过。"""
    resume = "Zhang - Python/PyTorch/Transformer/RAG/LangChain/FAISS - CS Master 2026 - looking for LLM intern"
    goal = "找大模型应用算法实习，深圳、北京"

    print("\n🚀 运行完整流水线...")
    report = run_full_pipeline(resume, goal, use_online=False)

    passed, issues = report.validate_contract()
    print(f"  decisions={len(report.job_decisions)} sources={len(report.jd_sources)}")
    print(f"  portfolio: safe={len(report.portfolio.safe)} stretch={len(report.portfolio.stretch)} hold={len(report.portfolio.hold)}")

    if not passed:
        print(f"\n❌ 合约未通过，{len(issues)} 个问题：")
        for iss in issues[:10]:
            print(f"  - {iss}")
    else:
        print("✅ 合约全部通过")

    assert passed, f"full pipeline contract should pass, got {len(issues)} issues"
    print("✅ test_full_pipeline_contract PASS")


def test_jd_source_stats():
    """确保 JD 来源中有 source_type 标注。"""
    resume = "Zhang - Python - CS 2026"
    report = run_full_pipeline(resume, goal="找个实习", use_online=False)

    types = set(s.source_type for s in report.jd_sources)
    print(f"  JD source types: {types}")
    assert len(types) > 0, "should have at least one source type"
    assert "Demo精选岗位" in types, f"should have Demo精选岗位, got {types}"
    print("✅ test_jd_source_stats PASS")


if __name__ == "__main__":
    test_no_source_no_recommend()
    test_rewrite_needs_evidence()
    test_job_decision_has_jd_evidence()
    test_resume_action_tagged()
    test_jd_source_stats()
    test_full_pipeline_contract()
    print("\n🎉 全部合约测试通过")
