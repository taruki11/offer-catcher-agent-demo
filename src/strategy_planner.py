"""
Strategy Planner Agent — 投递策略规划模块
生成：今日优先投递 Top3、稳妥/平衡/冲刺组合、7 天投递计划、
7 天面试准备计划、需要先改简历再投的岗位列表。
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _int(v, default: int = 0) -> int:
    """安全转换为 int。"""
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def _pick_top(ranked_jobs: list[dict], n: int = 3) -> list[dict]:
    """取 ApplyPriority 最高（或 score/apply_priority 字段）的前 n 个。"""
    key = _priority_key(ranked_jobs)
    sorted_jobs = sorted(ranked_jobs, key=lambda x: x.get(key, 0), reverse=True)
    return sorted_jobs[:n]


def _priority_key(ranked_jobs: list[dict]) -> str:
    """自动探测优先分数字段名。"""
    if not ranked_jobs:
        return "score"
    sample = ranked_jobs[0]
    if "apply_priority" in sample:
        return "apply_priority"
    if "score" in sample:
        return "score"
    return "score"


# ---------------------------------------------------------------------------
# 1. 今日优先投递 Top3
# ---------------------------------------------------------------------------

def gen_priority_top3(ranked_jobs: list[dict], profile: Optional[dict] = None) -> list[dict]:
    """
    返回每个 Top3 岗位 + 推荐动作说明：
      - apply_action: 立即投递 / 先优化再投 / 冲刺岗位 / 暂缓
    
    策略一致性保证：
      - 如果 Top1 是"立即投递"，则 Top2/3 不允许是"暂缓"
      - 如果 Top1 是"暂缓"，则 Top2/3 可以是"先优化再投"或"冲刺岗位"
    """
    top3 = _pick_top(ranked_jobs, 3)
    result = []
    
    # 第一遍：计算所有 action
    actions = []
    for job in top3:
        action = _infer_action(job, profile)
        actions.append((job, action))
    
    # 第二遍：策略一致性调整。Top3 是一个投递组合，不能同时出现
    # "立即投递"和"暂缓"这种互相打架的建议。
    if any(action == "立即投递" for _, action in actions) and any(action == "暂缓" for _, action in actions):
        actions = [
            (job, "先优化再投" if action == "暂缓" else action)
            for job, action in actions
        ]

    # 如果 Top1 本身都需要暂缓，说明整体匹配风险较高，后续岗位不应更激进。
    if actions and actions[0][1] == "暂缓":
        actions = [
            (job, "先优化再投" if action in {"立即投递", "冲刺岗位"} else action)
            for job, action in actions
        ]
    
    # 生成结果
    for job, action in actions:
        result.append({
            "rank": len(result) + 1,
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "apply_priority": job.get("apply_priority", job.get("score", 0)),
            "pass_score": job.get("pass_score", 0),
            "risk_score": job.get("risk_score", 0),
            "apply_action": action,
            "reason": _action_reason(job, action),
        })
    
    return result


def _infer_action(job: dict, profile: Optional[dict] = None) -> str:
    """
    基于 pass/risk/growth/missing_skills 推断投递动作。
    通用规则，不针对特定 case 硬编码。
    """
    pass_s = _int(job.get("pass_score"), 50)
    risk_s = _int(job.get("risk_score"), 50)
    growth_s = _int(job.get("growth_score"), 50)
    missing = job.get("missing_skills", [])
    missing_count = len(missing) if isinstance(missing, list) else 0

    if profile is None:
        profile = {}

    target_city = profile.get("_city", "")
    target_stage = profile.get("_stage", "")
    has_llm_project = bool(profile.get("has_llm_project", False))
    has_metrics = bool(profile.get("has_metrics", False))
    has_rec_project = bool(profile.get("has_rec_project", False))
    target_role = profile.get("_target_role", "")

    job_direction = job.get("direction") or ""
    job_stage = job.get("stage") or ""

    # 方向是否一致
    if target_role and job_direction:
        direction_match = (target_role in job_direction or job_direction in target_role)
    else:
        direction_match = False

    # 城市/阶段错位判断
    city_mismatch = bool(
        target_city and target_city != "不限" and job.get("city") != target_city
    )
    stage_mismatch = bool(
        target_stage and job_stage and job_stage != "不限" and job_stage != target_stage
    )

    # 已毕业判断
    is_graduated = any(kw in str(target_stage) for kw in ["已毕业", "校招", "2025"])

    # 已毕业 + 投实习 = 阶段错位
    if is_graduated and job_stage == "实习":
        stage_mismatch = True

    has_project_signal = has_llm_project or has_rec_project
    low_risk = risk_s <= 15
    medium_risk = risk_s <= 35
    strong_fit = pass_s >= 70 and low_risk and missing_count <= 1

    # ========== 1. 硬伤过滤：城市/阶段错位 ==========
    if city_mismatch or stage_mismatch:
        if strong_fit:
            return "冲刺岗位"
        if is_graduated and has_project_signal and has_metrics and pass_s >= 55 and risk_s <= 30 and missing_count <= 3:
            return "冲刺岗位"
        if pass_s >= 50 and medium_risk and missing_count <= 3:
            return "先优化再投"
        return "暂缓"

    # ========== 2. 方向不一致：先判断是否还有可迁移价值 ==========
    if target_role and not direction_match:
        if pass_s >= 50 and risk_s <= 25 and missing_count <= 2:
            return "先优化再投"
        if pass_s >= 35 and risk_s <= 45 and ("算法" in job_direction or "NLP" in job_direction or "计算机视觉" in job_direction):
            return "先优化再投"
        return "暂缓"

    # ========== 3. 立即投递：要求低风险且证据足 ==========
    if direction_match:
        if missing_count == 0 and pass_s >= 55 and risk_s <= 25:
            return "立即投递"
        if strong_fit:
            return "立即投递"
        # NLP/相关方向迁移到大模型岗位，若风险极低且有量化证据，可直接投。
        if has_metrics and risk_s <= 10 and pass_s >= 55 and missing_count <= 3:
            return "立即投递"

    # ========== 4. 有项目但证据不完整：优先先优化再投 ==========
    if not has_metrics and missing_count > 0:
        return "先优化再投"
    if missing_count >= 3 and pass_s < 70:
        return "先优化再投"

    # ========== 5. 冲刺岗位：成长高但仍有明显缺口 ==========
    if direction_match and has_project_signal and has_metrics and growth_s >= 70 and pass_s >= 55 and risk_s <= 35:
        return "冲刺岗位"
    if direction_match and has_llm_project and growth_s >= 75 and pass_s >= 45 and risk_s <= 45:
        return "冲刺岗位"

    # ========== 6. 兜底 ==========
    if pass_s < 30 or risk_s > 70:
        return "暂缓"
    if pass_s >= 40:
        return "先优化再投"
    return "暂缓"


def _action_reason(job: dict, action: str) -> str:
    if action == "立即投递":
        return f"PassScore={job.get('pass_score', '?')}，初筛通过潜力高，建议今日投递。"
    if action == "先优化再投":
        return f"RiskScore={job.get('risk_score', '?')}，建议先补齐 {', '.join(job.get('missing_skills', [])[:3])} 再投。"
    if action == "冲刺岗位":
        return f"GrowthScore={job.get('growth_score', '?')}，虽有一定风险，但成长价值高，可冲刺。"
    return "多项评分偏低，建议优先投递其他岗位后再考虑。"


# ---------------------------------------------------------------------------
# 2. 稳妥 / 平衡 / 冲刺 岗位组合
# ---------------------------------------------------------------------------

def gen_job_combo(ranked_jobs: list[dict]) -> dict:
    """
    按 ApplyPriority 将岗位分为三类（各取最高分 2-3 个）：
      - stable：PassScore ≥ 70 且 RiskScore ≤ 30
      - balanced：PassScore ≥ 55 且 RiskScore ≤ 55
      - challenge：GrowthScore ≥ 65（允许 PassScore 较低）
    """
    stable, balanced, challenge = [], [], []

    for job in ranked_jobs:
        pass_s = job.get("pass_score", 0)
        risk_s = job.get("risk_score", 100)
        growth_s = job.get("growth_score", 0)

        if pass_s >= 70 and risk_s <= 30 and len(stable) < 3:
            stable.append(_summarize(job))
        elif pass_s >= 55 and risk_s <= 55 and len(balanced) < 3:
            balanced.append(_summarize(job))
        elif growth_s >= 65 and len(challenge) < 3:
            challenge.append(_summarize(job))

    # 保底：如果某类为空，从剩余岗位里补
    all_summary = [_summarize(j) for j in ranked_jobs]
    if not stable:
        stable = all_summary[:2]
    if not balanced:
        balanced = all_summary[2:4] if len(all_summary) >= 4 else all_summary[:2]
    if not challenge:
        challenge = all_summary[:2]

    return {
        "稳妥岗（高通过率）": stable,
        "平衡岗（综合推荐）": balanced,
        "冲刺岗（高成长价值）": challenge,
    }


def _summarize(job: dict) -> dict:
    return {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "match_score": job.get("match_score", job.get("score", 0)),
        "pass_score": job.get("pass_score", 0),
        "risk_score": job.get("risk_score", 0),
        "growth_score": job.get("growth_score", 0),
        "apply_priority": job.get("apply_priority", 0),
    }


# ---------------------------------------------------------------------------
# 3. 7 天投递计划
# ---------------------------------------------------------------------------

def gen_7day_apply_plan(ranked_jobs: list[dict], profile: Optional[dict] = None) -> list[str]:
    """
    生成 7 天投递节奏计划，每天 1-2 条可操作步骤。
    """
    top5 = _pick_top(ranked_jobs, 5)
    names = [f"{j.get('title', '岗位')}({j.get('company', '')})" for j in top5]

    plan = [
        f"第 1 天：锁定今日优先投递 Top{len(top5)}，完善简历中 {', '.join(top5[0].get('matched_skills', ['相关技能'])[:3])} 的项目证据。",
        f"第 2 天：投递第 1 个岗位 {names[0] if names else '目标岗位'}，并针对第 2 个岗位优化简历关键词。",
        f"第 3 天：投递第 2 个岗位，同步准备 {top5[0].get('interview_themes', ['技术问题'])[0] if top5 else '技术问题'} 相关面试题。",
        f"第 4 天：根据前两天投递反馈（若有），调整第 3 个岗位简历版本，补充量化指标。",
        f"第 5 天：投递第 3 个岗位，开始准备行为面试（自我介绍、项目深挖）。",
        f"第 6 天：投递第 4-5 个岗位（或冲刺岗），整理所有投递记录到表格。",
        f"第 7 天：复盘本周投递效果，更新简历版本，规划下周投递策略。",
    ]
    return plan


# ---------------------------------------------------------------------------
# 4. 7 天面试准备计划
# ---------------------------------------------------------------------------

def gen_7day_interview_plan(ranked_jobs: list[dict], profile: Optional[dict] = None) -> list[str]:
    """
    基于 Top1 岗位的 interview_themes 生成 7 天面试准备计划。
    """
    if not ranked_jobs:
        return [f"第 {i} 天：请先运行匹配获取岗位信息。" for i in range(1, 8)]

    top = ranked_jobs[0]
    themes = top.get("interview_themes", ["算法基础", "项目深挖", "系统设计", "业务理解"])

    plan = [
        f"第 1 天：复盘 {top.get('direction', '目标方向')} 岗位 JD，整理关键词和项目证据清单。",
        f"第 2 天：准备 {themes[0] if len(themes) > 0 else '算法基础'}，讲清输入、模型、输出和可量化指标。",
        f"第 3 天：准备 {themes[1] if len(themes) > 1 else '项目深挖'}，覆盖数据、模型、评估、落地四个维度。",
        f"第 4 天：准备 {themes[2] if len(themes) > 2 else '系统设计'}，重点讲失败 case 和优化方案。",
        f"第 5 天：模拟 {top.get('company', '目标公司')} 算法题 3 道，限时 60 分钟。",
        "第 6 天：做一次 20 分钟项目深挖 mock，覆盖数据、模型、评估、落地。",
        "第 7 天：压缩成 1 分钟自我介绍、3 分钟项目介绍和 5 个高频追问答案。",
    ]
    return plan


# ---------------------------------------------------------------------------
# 5. 哪些岗位需要先改简历再投
# ---------------------------------------------------------------------------

def gen_resume_advice(ranked_jobs: list[dict]) -> list[dict]:
    """
    返回需要先改简历再投的岗位列表，附带具体改写建议。
    """
    advice = []
    for job in ranked_jobs:
        pass_s = job.get("pass_score", 50)
        risk_s = job.get("risk_score", 50)
        missing = job.get("missing_skills", [])
        if pass_s < 65 or risk_s >= 50 or missing:
            advice.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "pass_score": pass_s,
                "risk_score": risk_s,
                "missing_skills": missing[:4],
                "advice": _resume_fix_tips(job),
                "urgency": "高" if pass_s < 50 else ("中" if pass_s < 65 else "低"),
            })
    # 按紧急程度排序：高 > 中 > 低
    urgency_order = {"高": 0, "中": 1, "低": 2}
    advice.sort(key=lambda x: urgency_order.get(x["urgency"], 9))
    return advice


def _resume_fix_tips(job: dict) -> list[str]:
    tips = []
    missing = job.get("missing_skills", [])
    if missing:
        tips.append(f"补充 {missing[0]} 的真实项目经历或课程项目，不要只写「了解」。")
    if job.get("risk_score", 0) >= 50:
        tips.append("简历中项目描述缺少量化指标，建议补充 NDCG/HitRate/TopK 等具体数字。")
    if job.get("keyword_coverage", 1.0) < 0.4:
        tips.append(f"JD 关键词覆盖率偏低，建议在项目描述中自然嵌入：{', '.join(job.get('skills', [])[:4])}。")
    if not tips:
        tips.append("简历与岗位匹配度尚可，建议再压缩表达、突出亮点。")
    return tips


# ---------------------------------------------------------------------------
# 统一入口：生成完整策略包
# ---------------------------------------------------------------------------

def gen_strategy_package(ranked_jobs: list[dict], profile: Optional[dict] = None) -> dict:
    """一次性返回所有策略内容，供 report_generator 和 app.py 使用。"""
    return {
        "priority_top3": gen_priority_top3(ranked_jobs, profile),
        "job_combo": gen_job_combo(ranked_jobs),
        "apply_plan_7day": gen_7day_apply_plan(ranked_jobs, profile),
        "interview_plan_7day": gen_7day_interview_plan(ranked_jobs, profile),
        "resume_advice": gen_resume_advice(ranked_jobs),
    }
