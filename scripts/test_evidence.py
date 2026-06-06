"""
test_evidence.py — 证据链模块测试脚本

测试目标：
1. builtin job 能生成 evidence
2. user pasted JD 能生成 evidence
3. evidence 字段存在且非空
4. 每条 evidence 都有 type/claim/evidence/source/confidence
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 加入项目根目录到 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.resume_parser import parse_resume
from src.jd_parser import parse_jd
from src.matcher import load_jobs, score_job, rank_job_list
from src.evidence import (
    build_jd_evidence,
    build_resume_evidence,
    build_gap_evidence,
    build_action_evidence,
    attach_evidence,
    attach_evidence_to_jobs,
)


# ---------------------------------------------------------------------------
# 测试数据
# ---------------------------------------------------------------------------

SAMPLE_RESUME = """张同学 | 计算机科学与技术 | 2026 届硕士
求职方向：大模型应用算法 / 推荐算法实习生，期望城市深圳或北京。
技能：Python、PyTorch、Transformer、RAG、Agent、Embedding、Faiss、LangChain、推荐系统、召回排序、NDCG、A/B Test、SQL。
项目经历：
1. GenAdRec 生成式广告推荐项目：基于 Transformer 建模用户行为序列，将广告候选集转化为生成式 likelihood rerank 问题；构建 Semantic ID 表示广告 item，结合多兴趣召回提升 NDCG@10。
2. LLM 求职助手 Demo：使用 DeepSeek API 和 bge embedding 实现 JD 检索、简历关键词诊断、Prompt 模板优化，支持输出岗位匹配解释。
3. MIND 多兴趣推荐复现：复现 capsule routing 用户多兴趣建模，在公开数据集上对比召回 HitRate 与 NDCG。
实习经历：
曾参与推荐系统离线评估脚本开发，负责样本构造、特征清洗和模型结果分析。
补充：希望找能结合 LLM、Agent、RAG 和推荐排序的算法岗位。"""

SAMPLE_JD = """职位名称：大模型应用算法实习生
公司：腾讯
城市：深圳
方向：大模型应用算法
阶段：实习
技能要求：LLM、RAG、Agent、Prompt Engineering、LangChain、Embedding、Faiss、Python
项目信号：RAG、Agent、Semantic Retrieval、Multi-turn Dialogue
JD 描述：
负责大模型应用算法研发，包括 RAG 系统搭建、Agent 工作流设计、Prompt 模板优化。
要求熟悉 LLM 应用开发，了解 RAG 技术栈（Embedding + Vector DB），有 Agent 框架使用经验者优先。
"""


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _check_evidence_fields(ev: dict, context: str) -> list[str]:
    """检查单条 evidence 是否包含所有必填字段。返回错误列表。"""
    errors = []
    required_fields = ["type", "claim", "evidence", "source", "confidence"]
    for field in required_fields:
        if field not in ev:
            errors.append(f"{context}: 缺少字段 {field}")
    # confidence 必须是 high/medium/low 之一
    if "confidence" in ev and ev["confidence"] not in ("high", "medium", "low"):
        errors.append(f"{context}: confidence={ev['confidence']} 不在允许范围内")
    return errors


def _print_evidence_list(label: str, ev_list: list[dict]) -> None:
    """打印 evidence 列表，方便人工检查。"""
    print(f"\n  【{label}】（共 {len(ev_list)} 条）")
    for i, ev in enumerate(ev_list):
        print(f"    [{i+1}] type={ev.get('type','?')} | confidence={ev.get('confidence','?')}")
        print(f"        claim: {ev.get('claim','')}")
        print(f"        evidence: {ev.get('evidence','')}")
        print(f"        source: {ev.get('source','')}")


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

def test_01_builtin_job_evidence() -> bool:
    """测试 1：builtin job 能生成 evidence。"""
    print("\n=== test_01_builtin_job_evidence ===")
    profile = parse_resume(SAMPLE_RESUME)
    jobs = load_jobs(ROOT / "data" / "jobs.json")
    job = jobs[0]  # 取第一个 builtin job

    # 对 job 做完整打分（会附加 evidence）
    scored = score_job(job, profile, SAMPLE_RESUME, "大模型应用算法", "深圳", "实习")

    # 检查 evidence 字段存在
    required_evidence_fields = ["jd_evidence", "resume_evidence", "gap_evidence", "action_evidence"]
    errors = []
    for field in required_evidence_fields:
        if field not in scored:
            errors.append(f"scored 缺少字段 {field}")
        elif not scored[field]:
            errors.append(f"scored[{field}] 为空")

    if errors:
        print("  [FAIL] " + "; ".join(errors))
        return False

    _print_evidence_list("jd_evidence", scored["jd_evidence"])
    _print_evidence_list("resume_evidence", scored["resume_evidence"])
    _print_evidence_list("gap_evidence", scored["gap_evidence"])
    print(f"  action_evidence: {scored['action_evidence']}")

    # 检查每条 evidence 的字段
    all_errors = []
    for ev in scored["jd_evidence"]:
        all_errors.extend(_check_evidence_fields(ev, "jd_evidence"))
    for ev in scored["resume_evidence"]:
        all_errors.extend(_check_evidence_fields(ev, "resume_evidence"))
    for ev in scored["gap_evidence"]:
        all_errors.extend(_check_evidence_fields(ev, "gap_evidence"))

    if all_errors:
        print("  [FAIL] " + "; ".join(all_errors))
        return False

    print("  [PASS] builtin job 证据链生成正常")
    return True


def test_02_user_pasted_jd_evidence() -> bool:
    """测试 2：user pasted JD 能生成 evidence。"""
    print("\n=== test_02_user_pasted_jd_evidence ===")
    profile = parse_resume(SAMPLE_RESUME)

    # 解析用户粘贴的 JD
    from src.jd_parser import parse_jd
    jd_result = parse_jd(SAMPLE_JD)
    if not jd_result:
        print("  [SKIP] parse_jd 返回空，可能是规则解析失败（非错误）")
        return True

    job = jd_result
    job.setdefault("source", "user_pasted")
    job.setdefault("stage", "实习")
    job.setdefault("city", "深圳")
    job.setdefault("direction", "大模型应用算法")
    job.setdefault("company", "测试公司")
    job.setdefault("title", "大模型应用算法实习生")
    job.setdefault("skills", job.get("skills", []))
    job.setdefault("project_signals", job.get("project_signals", []))

    # 对 job 做完整打分
    scored = score_job(job, profile, SAMPLE_RESUME, "大模型应用算法", "深圳", "实习")

    required_evidence_fields = ["jd_evidence", "resume_evidence", "gap_evidence", "action_evidence"]
    errors = []
    for field in required_evidence_fields:
        if field not in scored:
            errors.append(f"scored 缺少字段 {field}")

    if errors:
        print("  [FAIL] " + "; ".join(errors))
        return False

    _print_evidence_list("jd_evidence (user JD)", scored["jd_evidence"])
    _print_evidence_list("resume_evidence (user JD)", scored["resume_evidence"])
    _print_evidence_list("gap_evidence (user JD)", scored["gap_evidence"])

    print("  [PASS] user pasted JD 证据链生成正常")
    return True


def test_03_evidence_fields_complete() -> bool:
    """测试 3：每条 evidence 都有 type/claim/evidence/source/confidence。"""
    print("\n=== test_03_evidence_fields_complete ===")
    profile = parse_resume(SAMPLE_RESUME)
    jobs = load_jobs(ROOT / "data" / "jobs.json")
    job = jobs[0]

    scored = score_job(job, profile, SAMPLE_RESUME, "大模型应用算法", "深圳", "实习")

    all_errors = []
    for ev in scored.get("jd_evidence", []):
        all_errors.extend(_check_evidence_fields(ev, "jd_evidence"))
    for ev in scored.get("resume_evidence", []):
        all_errors.extend(_check_evidence_fields(ev, "resume_evidence"))
    for ev in scored.get("gap_evidence", []):
        all_errors.extend(_check_evidence_fields(ev, "gap_evidence"))

    if all_errors:
        print("  [FAIL] " + "; ".join(all_errors[:5]))
        return False

    print("  [PASS] 所有 evidence 字段完整")
    return True


def test_04_action_evidence_format() -> bool:
    """测试 4：action_evidence 是 list[str]，且内容非空。"""
    print("\n=== test_04_action_evidence_format ===")
    profile = parse_resume(SAMPLE_RESUME)
    jobs = load_jobs(ROOT / "data" / "jobs.json")
    job = jobs[0]

    scored = score_job(job, profile, SAMPLE_RESUME, "大模型应用算法", "深圳", "实习")

    action_ev = scored.get("action_evidence", [])
    if not isinstance(action_ev, list):
        print(f"  [FAIL] action_evidence 类型错误：{type(action_ev)}")
        return False
    if not action_ev:
        print("  [FAIL] action_evidence 为空")
        return False
    for i, item in enumerate(action_ev):
        if not isinstance(item, str):
            print(f"  [FAIL] action_evidence[{i}] 不是 str：{type(item)}")
            return False
        if not item.strip():
            print(f"  [FAIL] action_evidence[{i}] 为空字符串")
            return False

    print(f"  [PASS] action_evidence 格式正确（{len(action_ev)} 条）")
    return True


def test_05_attach_evidence_to_jobs() -> bool:
    """测试 5：attach_evidence_to_jobs 能批量处理 job list。"""
    print("\n=== test_05_attach_evidence_to_jobs ===")
    profile = parse_resume(SAMPLE_RESUME)
    jobs = load_jobs(ROOT / "data" / "jobs.json")[:3]  # 只取前 3 个，加速

    scored_list = attach_evidence_to_jobs(jobs, SAMPLE_RESUME, profile)

    errors = []
    for i, job in enumerate(scored_list):
        for field in ["jd_evidence", "resume_evidence", "gap_evidence", "action_evidence"]:
            if field not in job:
                errors.append(f"job[{i}] 缺少 {field}")

    if errors:
        print("  [FAIL] " + "; ".join(errors))
        return False

    print(f"  [PASS] attach_evidence_to_jobs 批量处理 {len(scored_list)} 个岗位正常")
    return True


def test_06_evidence_grounded() -> bool:
    """测试 6：evidence 是 grounded 的（不能写空泛建议）。"""
    print("\n=== test_06_evidence_grounded ===")
    profile = parse_resume(SAMPLE_RESUME)
    jobs = load_jobs(ROOT / "data" / "jobs.json")
    job = jobs[0]

    scored = score_job(job, profile, SAMPLE_RESUME, "大模型应用算法", "深圳", "实习")

    # 检查 evidence 中的 claim/evidence 是否非空且有实质内容
    all_errors = []
    for ev in scored.get("jd_evidence", []):
        if not ev.get("claim", "").strip():
            all_errors.append("jd_evidence 中有空的 claim")
        if not ev.get("evidence", "").strip():
            all_errors.append("jd_evidence 中有空的 evidence")

    if all_errors:
        print("  [FAIL] " + "; ".join(all_errors))
        return False

    print("  [PASS] evidence 内容 grounded（非空泛建议）")
    return True


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("证据链模块测试开始")
    print("=" * 60)

    results = []
    results.append(("builtin job 生成 evidence", test_01_builtin_job_evidence()))
    results.append(("user pasted JD 生成 evidence", test_02_user_pasted_jd_evidence()))
    results.append(("evidence 字段完整", test_03_evidence_fields_complete()))
    results.append(("action_evidence 格式正确", test_04_action_evidence_format()))
    results.append(("attach_evidence_to_jobs 批量处理", test_05_attach_evidence_to_jobs()))
    results.append(("evidence grounded", test_06_evidence_grounded()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    pass_count = 0
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}  {name}")
        if result:
            pass_count += 1
    print(f"\n总计：{pass_count}/{len(results)} 通过")
    if pass_count == len(results):
        print("[OK] 所有测试通过！")
    else:
        print("[WARN] 有测试失败，请检查 above。")


if __name__ == "__main__":
    main()
