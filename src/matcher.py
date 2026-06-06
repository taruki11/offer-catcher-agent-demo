import json
import math
import os
from collections import Counter
from pathlib import Path

from src.resume_parser import contains

try:
    from src.conversion import attach_conversion_scores
except Exception:  # pragma: no cover — conversion 模块不存在时回退
    attach_conversion_scores = None


# ---------------------------------------------------------------------------
# 语义匹配器（可选，sentence_transformers 未安装时回退到 token 相似度）
# ---------------------------------------------------------------------------
_SEMANTIC_MATCHER = None
_ENABLE_EMBEDDING_CLIENT = os.getenv("ENABLE_EMBEDDING_CLIENT", "").lower() in {"1", "true", "yes"}
_ENABLE_LOCAL_SEMANTIC = os.getenv("ENABLE_LOCAL_SEMANTIC_MATCHER", "").lower() in {"1", "true", "yes"}
_TRY_LOAD_SEMANTIC = False  # 默认不加载，避免自动下载模型

# 主排序里的 embedding 能力必须显式开启，避免 API key 或缓存模型改变 core eval 结果。
if _ENABLE_LOCAL_SEMANTIC and os.getenv("SEMANTIC_MODEL_PATH"):
    _TRY_LOAD_SEMANTIC = True


def _get_semantic_matcher():
    """Lazy-load SemanticMatcher（避免导入时即失败）。"""
    global _SEMANTIC_MATCHER, _TRY_LOAD_SEMANTIC
    if not _TRY_LOAD_SEMANTIC:
        return _SEMANTIC_MATCHER
    _TRY_LOAD_SEMANTIC = False
    try:
        from src.semantic_matcher import SemanticMatcher
        _SEMANTIC_MATCHER = SemanticMatcher()
        print("[OK] SemanticMatcher loaded — using embedding-based semantic recall.")
    except Exception as exc:
        print(f"[WARN] SemanticMatcher not available ({exc}) — falling back to token cosine.")
        _SEMANTIC_MATCHER = None
    return _SEMANTIC_MATCHER


def semantic_similarity(resume_text: str, job_text: str) -> float:
    """语义相似度（优先 API/client，回退 embedding，最后 token cosine）。"""
    # 1) EmbeddingClient 默认关闭，避免误用 API 或自动加载未声明的 embedding 模型。
    if _ENABLE_EMBEDDING_CLIENT:
        try:
            from src.embedding_client import get_embedding_client
            _CLIENT = get_embedding_client()
            if _CLIENT.is_available():
                sim = _CLIENT.semantic_similarity(resume_text, job_text)
                if sim is not None:
                    return sim
        except Exception:
            pass

    # 2) SemanticMatcher（本地 sentence-transformers）
    matcher = _get_semantic_matcher()
    if matcher is not None:
        try:
            return matcher.compute_similarity(resume_text, job_text)
        except Exception:
            pass

    # 3) fallback：token cosine
    return cosine_similarity(resume_text, job_text)


WEIGHTS = {
    "技能匹配": 0.28,
    "项目匹配": 0.25,
    "经历匹配": 0.10,
    "方向匹配": 0.27,
    "成长潜力": 0.10,
}


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    tokens = []
    buff = []
    for char in text:
        if char.isascii() and char.isalnum():
            buff.append(char)
        else:
            if buff:
                tokens.append("".join(buff))
                buff = []
            if "\u4e00" <= char <= "\u9fff":
                tokens.append(char)
    if buff:
        tokens.append("".join(buff))
    return tokens


def cosine_similarity(left: str, right: str) -> float:
    left_counter = Counter(tokenize(left))
    right_counter = Counter(tokenize(right))
    if not left_counter or not right_counter:
        return 0.0
    keys = set(left_counter) | set(right_counter)
    dot = sum(left_counter[k] * right_counter[k] for k in keys)
    left_norm = math.sqrt(sum(v * v for v in left_counter.values()))
    right_norm = math.sqrt(sum(v * v for v in right_counter.values()))
    return dot / (left_norm * right_norm)


def load_jobs(jobs_path: Path) -> list[dict]:
    with jobs_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def overlap(required: list[str], actual: list[str], resume_text: str) -> list[str]:
    return [
        term
        for term in required
        if term in actual or contains(resume_text, term)
    ]


def score_job(job: dict, profile: dict, resume_text: str, target_role: str, target_city: str, stage: str) -> dict:
    matched_skills = overlap(job["skills"], profile["skills"], resume_text)
    missing_skills = [skill for skill in job["skills"] if skill not in matched_skills]
    matched_project = overlap(job["project_signals"], profile["project_signals"], resume_text)

    semantic_recall = semantic_similarity(resume_text, f"{job['title']} {job['jd']} {' '.join(job['skills'])}")
    skill_score = clamp_score((len(matched_skills) / max(len(job["skills"]), 1)) * 100)
    project_score = clamp_score(
        (len(matched_project) / max(len(job["project_signals"]), 1)) * 100
        + (8 if profile["has_metrics"] else 0)
        + semantic_recall * 12
    )
    experience_score = 86 if job["stage"] == stage else 68
    direction_score = 92 if job["direction"] == target_role else 40
    city_score = 88 if target_city == "不限" else 96 if job["city"] == target_city else 62
    preference_score = clamp_score(0.72 * direction_score + 0.28 * city_score)
    growth_score = clamp_score(
        48
        + min(len(profile["skills"]), 10) * 3
        + (12 if profile["has_llm_project"] else 0)
        + (8 if profile["has_rec_project"] else 0)
    )

    dimensions = {
        "技能匹配": skill_score,
        "项目匹配": project_score,
        "经历匹配": experience_score,
        "方向匹配": preference_score,
        "成长潜力": growth_score,
    }
    match_score = clamp_score(sum(dimensions[name] * weight for name, weight in WEIGHTS.items()))
    # direction match bonus: 目标方向岗位获得额外加分
    if job["direction"] == target_role:
        match_score = clamp_score(match_score + 15)
    # title match bonus: 精确匹配 target_role 的岗位加分最高；含额外方向词（如 Agent）的次之
    import re as _re
    title_lower = job["title"].lower()
    target_lower = target_role.lower()
    title_exact_match = False
    if target_lower in title_lower:
        # 精确匹配：title 去掉「实习生/工程师」后缀后与 target_role 高度一致
        title_clean = _re.sub(r"(实习生|工程师|生|员)$", "", job["title"]).lower()
        target_clean = _re.sub(r"(实习生|工程师|生|员)$", "", target_role).lower()
        if target_clean in title_clean or title_clean in target_clean:
            match_score = clamp_score(match_score + 20)
            title_exact_match = True
        else:
            # 模糊匹配（如 target=大模型应用算法，title=大模型 Agent 应用实习生）
            match_score = clamp_score(match_score + 6)
    else:
        title_exact_match = False

    # 迁移型强匹配补偿：当用户目标方向较宽，但某个非目标方向岗位在技能和项目上
    # 明显更贴合简历时，不能只因 direction 字段不同被平台/泛算法岗位压下去。
    if job["direction"] != target_role and skill_score >= 75 and project_score >= 70:
        match_score = clamp_score(match_score + 5)

    # 基础返回值
    scored = dict(job)
    scored.update(
        {
            "match_score": match_score,
            "score": match_score,  # 保留兼容
            "growth_score": growth_score,
            "semantic_recall": round(semantic_recall, 4),
            "target_role": target_role,
            "target_city": target_city,
            "target_stage": stage,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "dimensions": dimensions,
            "strengths": build_strengths(job, matched_skills, profile),
            "gaps": build_gaps(job, missing_skills, profile),
            "rewrites": build_rewrites(job, matched_skills, missing_skills),
            "interview_plan": build_interview_plan(job, missing_skills),
        }
    )

    # 附加 conversion 分数（PassScore / RiskScore / KeywordCoverage / GrowthScore）
    if attach_conversion_scores is not None:
        try:
            conv = attach_conversion_scores(
                profile=profile,
                job=scored,
                resume_text=resume_text,
                target_role=target_role,
                target_city=target_city,
                stage=stage,
            )
            # 安全赋值：过滤 None 值（conv 返回值可能包含显式 None）
            _conv_map = {
                "pass_score": 50,
                "risk_score": 50,
                "growth_score": growth_score,
                "keyword_coverage": 0.0,
            }
            for key, default in _conv_map.items():
                val = conv.get(key) if isinstance(conv, dict) else None
                # 关键：val is None 时用 default（不仅 key 不存在，值本身为 None 也要覆盖）
                scored[key] = default if val is None else val
        except Exception as e:
            import sys
            print(f"[WARN] attach_conversion_scores failed: {e}", file=sys.stderr)
            scored.setdefault("pass_score", 50)
            scored.setdefault("risk_score", 50)
            scored.setdefault("growth_score", growth_score)
            scored.setdefault("keyword_coverage", 0.0)
    else:
        scored.setdefault("pass_score", 50)
        scored.setdefault("risk_score", 50)
        scored.setdefault("keyword_coverage", 0.0)

    # 计算 ApplyPriority（确保 growth_score 不为 None）
    ps = scored.get("pass_score", 50)
    rs = scored.get("risk_score", 50)
    gs = scored.get("growth_score")
    if gs is None:
        gs = growth_score  # 使用 score_job 本地计算的 growth_score
        scored["growth_score"] = gs  # 写回字典，防止后续读者读到 None
    ms = scored.get("match_score", match_score)
    apply_priority = round(0.40 * ms + 0.30 * ps - 0.15 * rs + 0.15 * gs, 2)

    # title_exact_match bonus：精确匹配 target_role 的岗位在 apply_priority 上加权重，
    # 防止 match_score 被 clamp_score 封顶后无法区分精确/模糊匹配
    if title_exact_match:
        apply_priority = round(apply_priority + 1.5, 2)
    scored["apply_priority"] = apply_priority

    # 附加证据链（Evidence Chain）
    try:
        from src.evidence import attach_evidence
        scored = attach_evidence(scored, resume_text, profile)
    except Exception:
        pass

    # 标记 title 精确匹配，供排序破 tie 使用
    scored["title_exact_match"] = title_exact_match

    return scored


def rank_jobs(
    resume_text: str,
    profile: dict,
    target_role: str,
    target_city: str,
    stage: str,
    top_k: int,
    jobs_path: Path,
) -> list[dict]:
    """
    返回全部打分后的岗位列表（按 apply_priority 降序）。
    调用方可根据需要用 sorted() 构造 by_match / by_priority 两个榜单。
    """
    jobs = load_jobs(jobs_path)
    scored_jobs = [
        score_job(job, profile, resume_text, target_role, target_city, stage)
        for job in jobs
    ]
    # 默认按 apply_priority 降序排列，title_exact_match=True 的岗位排在同分前
    scored_jobs.sort(
        key=lambda item: (
            item.get("apply_priority", item.get("score", 0)),
            int(item.get("title_exact_match", False)),
        ),
        reverse=True,
    )
    return scored_jobs[:top_k]


def rank_job_list(
    resume_text: str,
    profile: dict,
    target_role: str,
    target_city: str,
    stage: str,
    top_k: int,
    jobs: list[dict],
) -> list[dict]:
    """
    对传入的 jobs list 打分排序（不读取文件）。
    与 rank_jobs 参数兼容，jobs_path 替换为 jobs 列表。
    """
    scored_jobs = [
        score_job(job, profile, resume_text, target_role, target_city, stage)
        for job in jobs
    ]
    scored_jobs.sort(
        key=lambda item: (
            item.get("apply_priority", item.get("score", 0)),
            int(item.get("title_exact_match", False)),
        ),
        reverse=True,
    )
    return scored_jobs[:top_k]


def build_strengths(job: dict, matched_skills: list[str], profile: dict) -> list[str]:
    strengths = []
    if matched_skills:
        strengths.append(f"命中核心技能：{'、'.join(matched_skills[:6])}，具备进入岗位精排池的基础。")
    if profile["has_llm_project"] and "大模型" in job["direction"]:
        strengths.append("简历中已有 LLM/RAG/Agent 信号，能对齐大模型应用算法岗位。")
    if profile["has_rec_project"] and ("推荐" in job["direction"] or "匹配" in job["jd"]):
        strengths.append("推荐系统、召回排序、语义表征经历可以迁移到人岗匹配推荐。")
    if profile["has_metrics"]:
        strengths.append("项目描述包含 NDCG、HitRate、TopK 等指标，便于证明算法效果。")
    return strengths or ["当前简历具备基础技术栈，但需要补充更明确的项目证据。"]


def build_gaps(job: dict, missing_skills: list[str], profile: dict) -> list[str]:
    gaps = []
    if missing_skills:
        gaps.append(f"岗位还要求 {'、'.join(missing_skills[:5])}，建议补充真实项目或技能证据。")
    if not profile["has_metrics"]:
        gaps.append("项目缺少可量化指标，容易被认为只是功能实现。")
    if "Agent" in job["jd"] and "Agent" not in profile["project_signals"]:
        gaps.append("Agent 工作流表达不够突出，需要说明任务拆解、工具调用和失败兜底。")
    return gaps or ["暂无明显硬伤，建议继续压缩表达并突出岗位关键词。"]


def build_rewrites(job: dict, matched_skills: list[str], missing_skills: list[str]) -> list[dict]:
    skills = job.get("skills") or ["岗位相关技能"]
    main_skill = matched_skills[0] if matched_skills else skills[0]
    missing = missing_skills[0] if missing_skills else skills[-1]
    return [
        {
            "before": "负责推荐系统建模和模型结果分析。",
            "after": f"围绕 {job['direction']} 场景，使用 {main_skill} 构建候选召回与精排链路，并通过 NDCG@10 / TopK 命中率评估模型收益。",
        },
        {
            "before": "做过一个 LLM 求职助手 Demo。",
            "after": "设计多 Agent 求职匹配流程，将简历解析、JD 理解、岗位排序、能力缺口诊断和简历优化拆成可解释节点。",
        },
        {
            "before": "熟悉大模型相关技术。",
            "after": f"熟悉 {'、'.join(skills[:4])}，可独立完成 Prompt 模板、结构化输出、检索增强和结果评估配置。",
        },
        {
            "before": "技能栏可以继续补充。",
            "after": f"若确有实践，建议补充 {missing}，并用一次实验、接口调用或离线评估证明不是仅停留在概念层。",
        },
    ]


def build_interview_plan(job: dict, missing_skills: list[str]) -> list[str]:
    themes = job.get("interview_themes", ["算法基础", "项目深挖", "系统设计", "业务理解"])
    if not themes or len(themes) < 2:
        themes = ["算法基础", "项目深挖", "系统设计", "业务理解"]
    skills = job.get("skills") or ["岗位相关技能"]
    focus = missing_skills[:3] or skills[:3]
    if not focus:
        focus = ["岗位相关技能"]
    return [
        f"第 1 天：复盘 {job['direction']} 岗位 JD，整理关键词和项目证据。",
        f"第 2 天：准备 {themes[0]}，讲清输入、模型、输出和指标。",
        f"第 3 天：补齐 {focus[0]} 的实践案例，写成可追问的简历 bullet。",
        f"第 4 天：准备 {themes[1]}，重点讲失败 case 和优化方案。",
        f"第 5 天：针对 {job['company']} 场景模拟 3 个算法方案题。",
        "第 6 天：做一次 20 分钟项目深挖 mock，覆盖数据、模型、评估、落地。",
        "第 7 天：压缩成 1 分钟自我介绍、3 分钟项目介绍和 5 个高频追问答案。",
    ]
