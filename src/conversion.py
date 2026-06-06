"""
Conversion Agent — 简历转化率优化模块（v2：校准分数，减少跨方向过度惩罚）
计算 PassScore（简历初筛通过潜力）、KeywordCoverage（JD 关键词覆盖率）、
RiskScore（投递风险，越高越危险），供 Application Ranker Agent 使用。
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

_SKILL_TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-\+/]+(?:\s*[+/]\s*[a-zA-Z0-9_\-\+]+)*")


def _tokenize(text: str) -> list[str]:
    """小写、ASCII 词 + 中文字符分离。"""
    tokens: list[str] = []
    buf = []
    for ch in (text or "").lower():
        if ch.isascii() and (ch.isalnum() or ch in "_-+/"):
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf))
                buf = []
            if "\u4e00" <= ch <= "\u9fff":
                tokens.append(ch)
    if buf:
        tokens.append("".join(buf))
    return tokens


def _counter(text: str) -> Counter:
    return Counter(_tokenize(text))


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in set(a) | set(b))
    norm_a = sum(v * v for v in a.values()) ** 0.5
    norm_b = sum(v * v for v in b.values()) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# ---------------------------------------------------------------------------
# PassScore：简历初筛通过潜力（0-100，越高越好）
# ---------------------------------------------------------------------------

def calc_pass_score(profile: dict, job: dict, resume_text: Optional[str] = None) -> int:
    """
    基于简历结构化画像 + JD，估算 HR/系统初筛通过概率对应的分数。

    v2 校准：
      - 降低「阶段不一致」的惩罚（从 -10 改为更温和的处理）
      - 跨方向转移（如 CV→LLM）不应过度扣分
      - 纯推荐/纯后端选手投 AI 平台岗位，技能命中率应合理计算
    """
    score = 0

    skills = job.get("skills", [])
    matched = [s for s in skills if s in profile.get("skills", [])]
    if skills:
        hit_rate = len(matched) / len(skills)
        score += int(35 * min(hit_rate, 1.0))  # 权重从 30 提升到 35

    project_sigs = job.get("project_signals", job.get("project_signals", []))
    if project_sigs:
        matched_proj = [s for s in project_sigs if s in profile.get("project_signals", [])]
        score += int(20 * min(len(matched_proj) / len(project_sigs), 1.0))

    if profile.get("has_metrics"):
        score += 15

    # v2：跨方向转移时，只要有 LLM 项目信号就加分（而不是只加「方向完全一致」）
    direction = job.get("direction", "")
    if "大模型" in direction or "LLM" in direction or "Agent" in direction:
        if profile.get("has_llm_project"):
            score += 15
        elif profile.get("has_rec_project"):  # 推荐→LLM 转移也加分
            score += 8
    elif "推荐" in direction:
        if profile.get("has_rec_project"):
            score += 10
    elif "后端" in direction or "Go" in direction or "Python" in direction:
        # 后端岗位：有 Python/Go/微服务项目就加分
        if profile.get("has_backend_project") or "Python" in profile.get("skills", []):
            score += 12

    if job.get("stage") == profile.get("_stage", ""):
        score += 10

    # 保底 20 分，避免全零
    return max(20, min(100, score))


# ---------------------------------------------------------------------------
# KeywordCoverage：JD 关键词在简历中的覆盖率（0.0-1.0）
# ---------------------------------------------------------------------------

def calc_keyword_coverage(resume_text: str, job: dict) -> float:
    if not resume_text:
        return 0.0

    jd_text = job.get("jd", "")
    skill_tokens = _tokenize(" ".join(job.get("skills", [])))
    jd_tokens = _tokenize(jd_text)
    all_tokens = Counter(skill_tokens + jd_tokens)

    resume_counter = _counter(resume_text)

    if not all_tokens:
        return 0.0

    hit = sum(1 for t in all_tokens if resume_counter.get(t, 0) > 0)
    return round(hit / max(len(all_tokens), 1), 4)


# ---------------------------------------------------------------------------
# RiskScore：投递风险（0-100，越高越危险）
# ---------------------------------------------------------------------------

def calc_risk_score(profile: dict, job: dict, resume_text: Optional[str] = None) -> int:
    """
    投递风险分：越高表示这份简历投这个岗位越容易炮灰/被刷。

    v2 校准：
      - 跨方向转移（CV→LLM、后端→AI平台）不应过度惩罚
      - 「无量化指标」扣 15（原来 20），避免过度惩罚
      - 「阶段不一致」扣 20（原来 30），更温和
    """
    risk = 0

    skills = job.get("skills", [])
    matched = [s for s in skills if s in profile.get("skills", [])]
    hit_rate = len(matched) / max(len(skills), 1)
    if hit_rate < 0.2:
        risk += 30  # 极低命中率，高风险
    elif hit_rate < 0.4:
        risk += 15  # 原来 25，降低
    elif hit_rate < 0.6:
        risk += 5   # 原来 10，降低

    if not profile.get("has_metrics"):
        risk += 15  # 原来 20，降低

    project_sigs = job.get("project_signals", job.get("project_signals", []))
    if project_sigs:
        matched_proj = [s for s in project_sigs if s in profile.get("project_signals", [])]
        if not matched_proj:
            # v2：跨方向时，有相关项目（哪怕不是完全匹配）也不扣分
            direction = job.get("direction", "")
            if "大模型" in direction and profile.get("has_llm_project"):
                pass  # 有 LLM 项目，不扣分
            elif "推荐" in direction and profile.get("has_rec_project"):
                pass  # 有推荐项目，不扣分
            else:
                risk += 10  # 原来 15，降低

    if job.get("stage") != profile.get("_stage", "") and job.get("stage") != "不限":
        risk += 20  # 原来 30，降低

    jd_text = job.get("jd", "").lower()
    if any(kw in jd_text for kw in ["agent", "工具调用", "多轮", "tool"]):
        if not profile.get("has_llm_project"):
            risk += 8  # 原来 10，降低

    if resume_text and len(resume_text.strip()) < 300:
        risk += 8  # 原来 10，降低

    if job.get("city") and job.get("city") != profile.get("_city", "") and job.get("stage") != "不限":
        risk += 5

    return min(100, max(0, risk))


# ---------------------------------------------------------------------------
# GrowthScore：成长/冲刺价值（0-100，越高越值得冲刺）
# ---------------------------------------------------------------------------

def calc_growth_score(profile: dict, job: dict) -> int:
    """
    冲刺价值分：岗位方向是否有助于能力成长、是否值得「跳一跳」投。

    v2 校准：
      - 跨方向转移（CV→LLM、后端→AI平台）应该有更高的 growth（值得冲刺）
      - 纯推荐/纯后端选手投 AI 平台岗位，growth 应该反映「学习空间」
    """
    score = 0

    skills = job.get("skills", [])
    matched = [s for s in skills if s in profile.get("skills", [])]
    if skills:
        miss_rate = 1.0 - len(matched) / len(skills)
        if 0.3 <= miss_rate <= 0.7:
            score += 30  # 适度挑战
        elif miss_rate > 0.7:
            score += 15  # 原来 10，提高（值得冲刺）
        else:
            score += 20  # 高命中率，成长空间一般

    direction = job.get("direction", "")
    target = profile.get("_target_role", "")

    # v2：跨方向匹配也加分
    if direction == target:
        score += 25
    elif target in direction or direction in target:
        score += 20  # 原来 15，提高
    elif "大模型" in direction and profile.get("has_llm_project"):
        score += 15  # 有 LLM 项目，跨方向也加分
    elif "推荐" in direction and profile.get("has_rec_project"):
        score += 10

    jd_text = job.get("jd", "").lower()
    if any(kw in jd_text for kw in ["agent", "llm", "排序", "召回", "rag"]):
        if profile.get("has_llm_project") or profile.get("has_rec_project"):
            score += 20

    if job.get("stage") == profile.get("_stage", ""):
        score += 15

    if job.get("city") == profile.get("_city", ""):
        score += 10

    return max(10, min(100, score))


# ---------------------------------------------------------------------------
# 统一入口：对一个 job 计算所有转化相关分数
# ---------------------------------------------------------------------------

def attach_conversion_scores(
    jobs: list[dict] | dict | None = None,
    profile: Optional[dict] = None,
    resume_text: Optional[str] = None,
    target_role: str = "",
    target_city: str = "",
    stage: str = "",
    job: Optional[dict] = None,
) -> list[dict] | dict:
    """
    给 job 或 jobs 附加 PassScore / RiskScore / GrowthScore / KeywordCoverage。

    兼容两种调用：
      - attach_conversion_scores(job=one_job, profile=...)
      - attach_conversion_scores(jobs_list, profile=...)
    """
    prof = dict(profile) if profile else {}
    prof["_stage"] = stage
    prof["_city"] = target_city
    prof["_target_role"] = target_role

    single = False
    if job is not None:
        jobs_list = [job]
        single = True
    elif isinstance(jobs, dict):
        jobs_list = [jobs]
        single = True
    else:
        jobs_list = list(jobs or [])

    result = []
    for item in jobs_list:
        pass_score = calc_pass_score(prof, item, resume_text)
        risk_score = calc_risk_score(prof, item, resume_text)
        growth_score = calc_growth_score(prof, item)
        kw_cov = calc_keyword_coverage(resume_text or "", item)

        j = dict(item)
        j["pass_score"] = pass_score
        j["risk_score"] = risk_score
        j["growth_score"] = growth_score
        j["keyword_coverage"] = kw_cov
        result.append(j)
    return result[0] if single and result else ({} if single else result)
