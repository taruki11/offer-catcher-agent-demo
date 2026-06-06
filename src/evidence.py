"""
Evidence Chain Module — 为每条建议/缺口/匹配结果附加可解释证据。

设计原则：
1. 所有证据都是 grounded 的，不能写空泛建议
2. 每条 evidence 包含：type, claim, evidence, source, confidence
3. evidence 可以附加到 job dict 上，由 app.py 渲染
"""

from __future__ import annotations

from typing import Any, Optional


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _make_evidence(
    evidence_type: str,
    claim: str,
    evidence: str,
    source: str,
    confidence: str = "high",
) -> dict:
    """
    构造一条证据。

    :param evidence_type: 证据类型，如 "skill_match", "gap", "action", "jd_requirement"
    :param claim: 主张，如 "命中 RAG"
    :param evidence: 证据内容，如 "简历中出现 "RAG""
    :param source: 来源，如 "resume", "jd", "rule"
    :param confidence: 置信度，"high", "medium", "low"
    """
    return {
        "type": evidence_type,
        "claim": claim,
        "evidence": evidence,
        "source": source,
        "confidence": confidence,
    }


def _find_term_in_text(term: str, text: str) -> bool:
    """检查 term 是否出现在 text 中（大小写不敏感）。"""
    if not term or not text:
        return False
    return term.lower() in text.lower()


def _snippet(text: str, term: str, window: int = 20, tail: int = 40) -> str:
    """从 text 中抽取包含 term 的片段（前后各 window/tail 字符）。"""
    if not term or term.lower() not in text.lower():
        return ""
    idx = text.lower().index(term.lower())
    start = max(0, idx - window)
    end = min(len(text), idx + len(term) + tail)
    return text[start:end].replace("\n", " ").strip()


# ---------------------------------------------------------------------------
# 1. JD Evidence — 这个岗位为什么要求这些技能
# ---------------------------------------------------------------------------

def build_jd_evidence(job: dict, resume_text: str, profile: dict) -> list[dict]:
    """
    根据 JD 文本，生成『为什么这个岗位要求这些技能』的证据列表。
    """
    evidences = []
    jd_text = job.get("jd", "")
    skills = job.get("skills", [])

    for skill in skills[:6]:
        claim = f"岗位要求 {skill} 技能"
        evidence_str = f"JD 中包含关键词「{skill}」"
        snippet_str = _snippet(jd_text, skill)
        if snippet_str:
            evidence_str = f"JD 原文片段：「...{snippet_str}...」"

        evidences.append(_make_evidence(
            evidence_type="jd_requirement",
            claim=claim,
            evidence=evidence_str,
            source="jd",
            confidence="high",
        ))

    # 方向证据
    direction = job.get("direction", "")
    if direction:
        evidences.append(_make_evidence(
            evidence_type="jd_direction",
            claim=f"岗位方向为 {direction}",
            evidence=f"JD 方向字段为「{direction}」",
            source="jd",
            confidence="high",
        ))

    return evidences


# ---------------------------------------------------------------------------
# 2. Resume Evidence — 用户简历中哪些内容支持匹配
# ---------------------------------------------------------------------------

def build_resume_evidence(job: dict, resume_text: str, profile: dict) -> list[dict]:
    """
    根据简历文本和 profile，生成『简历中哪些内容支持匹配』的证据列表。
    """
    evidences = []
    matched_skills = job.get("matched_skills", [])
    skills = job.get("skills", [])

    if not matched_skills and profile.get("skills"):
        matched_skills = [s for s in skills if s in profile.get("skills", [])]

    for skill in matched_skills[:6]:
        claim = f"简历中包含 {skill} 相关经历"
        evidence_str = f"简历中检测到关键词「{skill}」"
        snippet_str = _snippet(resume_text, skill)
        if snippet_str:
            evidence_str = f"简历原文片段：「...{snippet_str}...」"

        evidences.append(_make_evidence(
            evidence_type="resume_skill_match",
            claim=claim,
            evidence=evidence_str,
            source="resume",
            confidence="high",
        ))

    if profile.get("has_metrics"):
        evidences.append(_make_evidence(
            evidence_type="resume_metrics",
            claim="简历中包含量化指标",
            evidence="简历中检测到 NDCG/HitRate/准确率/提升x% 等量化描述",
            source="resume",
            confidence="high",
        ))

    if profile.get("has_llm_project"):
        evidences.append(_make_evidence(
            evidence_type="resume_llm_project",
            claim="简历中包含 LLM/RAG/Agent 项目",
            evidence="简历中检测到 LLM/RAG/Agent/Prompt 等相关关键词",
            source="resume",
            confidence="high",
        ))

    return evidences


# ---------------------------------------------------------------------------
# 3. Gap Evidence — 为什么说缺这些能力
# ---------------------------------------------------------------------------

def build_gap_evidence(job: dict, resume_text: str, profile: dict) -> list[dict]:
    """
    生成『为什么说缺这些能力』的证据列表。

    保证返回值非空：即使无明显缺口，也返回一条 "暂无明显硬伤" 证据。
    """
    evidences = []
    missing_skills = job.get("missing_skills", [])

    # 情况 A：有 missing_skills → 逐条生成缺口证据
    if missing_skills:
        for skill in missing_skills[:5]:
            claim = f"缺少 {skill} 相关能力或证据"
            evidence_str = f"JD 要求 {skill}，但简历中未检测到 {skill} 相关描述"
            snippet_str = _snippet(job.get("jd", ""), skill)
            if snippet_str:
                evidence_str = (
                    f"JD 要求：「...{snippet_str}...」，"
                    f"但简历中未检测到 {skill} 相关描述"
                )
            evidences.append(_make_evidence(
                evidence_type="gap_missing_skill",
                claim=claim,
                evidence=evidence_str,
                source="jd+resume",
                confidence="high",
            ))
        # 如果 profile 中 has_metrics 为 False，加一条
        if not profile.get("has_metrics"):
            evidences.append(_make_evidence(
                evidence_type="gap_no_metrics",
                claim="项目缺少可量化指标",
                evidence="简历中未检测到 NDCG/HitRate/准确率/提升x% 等量化描述",
                source="resume",
                confidence="high",
            ))
        return evidences

    # 情况 B：无 missing_skills，但 has_metrics=False → 量化缺口
    if not profile.get("has_metrics"):
        evidences.append(_make_evidence(
            evidence_type="gap_no_metrics",
            claim="项目缺少可量化指标",
            evidence="简历中未检测到 NDCG/HitRate/准确率/提升x% 等量化描述",
            source="resume",
            confidence="high",
        ))
        return evidences

    # 情况 C：无 missing_skills，has_metrics=True，但 JD 有 Agent 且简历无 Agent 信号
    if ("Agent" in job.get("jd", "")) and ("Agent" not in profile.get("project_signals", [])):
        evidences.append(_make_evidence(
            evidence_type="gap_agent",
            claim="Agent 工作流表达不够突出",
            evidence="JD 中包含 Agent 关键词，但简历项目信号中未检测到 Agent 相关描述",
            source="jd+resume",
            confidence="medium",
        ))
        return evidences

    # 情况 D：无 missing_skills，且上述都不满足 → 暂无明显缺口（必须返回非空）
    evidences.append(_make_evidence(
        evidence_type="gap_none",
        claim="暂无明显能力缺口",
        evidence=f"简历技能 {', '.join(job.get('matched_skills', [])[:4])} 覆盖岗位主要要求",
        source="resume+jd",
        confidence="high",
    ))
    return evidences


# ---------------------------------------------------------------------------
# 4. Action Evidence — 为什么建议立即投/先优化/冲刺/暂缓
# ---------------------------------------------------------------------------

def build_action_evidence(job: dict) -> list[str]:
    """
    生成『为什么建议这个动作』的依据列表（文本形式，简化用于 UI 展示）。
    """
    evidences = []
    pass_score = job.get("pass_score", 50)
    risk_score = job.get("risk_score", 50)
    growth_score = job.get("growth_score", 50)
    missing_skills = job.get("missing_skills", [])
    matched_skills = job.get("matched_skills", [])

    # 动作判断（与 strategy_planner._infer_action 逻辑对齐）
    if pass_score >= 70 and risk_score <= 30 and len(missing_skills) <= 2:
        evidences.append(
            f"PassScore={pass_score}≥70 且 RiskScore={risk_score}≤30，"
            f"初筛通过率高，建议立即投递。"
        )
    elif pass_score >= 40 and risk_score <= 55:
        missing_str = "、".join(missing_skills[:3]) if missing_skills else "部分技能"
        evidences.append(
            f"PassScore={pass_score}≥40 且 RiskScore={risk_score}≤55，"
            f"建议先优化简历再投递（补齐 {missing_str}）。"
        )
    elif growth_score >= 65 and risk_score <= 60:
        evidences.append(
            f"GrowthScore={growth_score}≥65，岗位成长价值高，可作为冲刺目标。"
        )
    else:
        evidences.append(
            f"PassScore={pass_score}、RiskScore={risk_score}，"
            "多项评分偏低，建议优先投递其他岗位。"
        )

    # 附加匹配/缺口依据
    if matched_skills:
        evidences.append(f"匹配技能：{', '.join(matched_skills[:4])}，具备岗位基础要求。")
    if missing_skills:
        evidences.append(f"缺失技能：{', '.join(missing_skills[:4])}，建议补充相关项目证据。")

    return evidences


# ---------------------------------------------------------------------------
# 5. Attach Evidence — 将证据链附加到 job dict 上
# ---------------------------------------------------------------------------

def attach_evidence(job: dict, resume_text: str, profile: dict) -> dict:
    """
    将 jd_evidence / resume_evidence / gap_evidence / action_evidence
    附加到 job dict 上，返回新的 job dict（不修改原 dict）。

    附加的字段：
    - jd_evidence: list[dict]
    - resume_evidence: list[dict]
    - gap_evidence: list[dict]
    - action_evidence: list[str]
    """
    job_with_evidence = dict(job)

    job_with_evidence["jd_evidence"] = build_jd_evidence(
        job_with_evidence, resume_text, profile
    )
    job_with_evidence["resume_evidence"] = build_resume_evidence(
        job_with_evidence, resume_text, profile
    )
    job_with_evidence["gap_evidence"] = build_gap_evidence(
        job_with_evidence, resume_text, profile
    )
    job_with_evidence["action_evidence"] = build_action_evidence(
        job_with_evidence
    )

    return job_with_evidence


# ---------------------------------------------------------------------------
# 6. 批量附加证据链（供 matcher.py 调用）
# ---------------------------------------------------------------------------

def attach_evidence_to_jobs(
    jobs: list[dict],
    resume_text: str,
    profile: dict,
) -> list[dict]:
    """
    对一个 job list 批量附加证据链。
    供 matcher.rank_job_list() 或 app.py 调用。
    """
    return [
        attach_evidence(job, resume_text, profile)
        for job in jobs
    ]
