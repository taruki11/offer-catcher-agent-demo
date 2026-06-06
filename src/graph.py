"""
graph.py — LangGraph Supervisor 模式 5 Agent 求职决策工作流

架构对齐：
- JobAgent-MultiAgent (connwang7): Supervisor + 5 专业 Agent
- langgraph-multi-agent-career-assistant (fineTuningForever): Send 并行 + 低分回路
"""

import json
from pathlib import Path
from typing import Literal
from langgraph.graph import StateGraph, END
from agent_state import AgentState, CareerIntent, JDProfile, ResumeEvidence, MatchResult
from agent_state import CounterfactualPlan, CoachOutput, InterviewPrep, StrategyOutput


# ======================================================================
# 核心知识库 — 从本地 corpus 加载
# ======================================================================

def _load_jobs() -> list[dict]:
    for fname in ("jobs_corpus.json", "jobs_merged.json", "jobs.json"):
        path = Path(__file__).resolve().parent.parent / "data" / fname
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return []


# ======================================================================
# JobAnalyzer — 方向推断 + 岗位匹配
# ======================================================================

_KEYWORDS_DIRECTION = {
    "Agent算法": ["langgraph", "agent", "multi agent", "智能体", "function calling", "tool"],
    "LLM应用算法": ["rag", "langchain", "llamaindex", "embedding", "faiss", "prompt"],
    "大模型算法": ["transformer", "pytorch", "finetune", "微调", "sft", "dpo", "rlhf"],
    "推荐算法": ["推荐", "recommend", "recall", "排序", "ctr"],
}

def _node_job_analyzer(state: AgentState) -> AgentState:
    """推断求职方向 + 加载匹配岗位。"""
    resume = state.resume_text.lower()
    goal = (state.user_goal or "").lower()

    # 方向推断
    direction = "大模型应用算法"
    for d, kws in _KEYWORDS_DIRECTION.items():
        if any(k in resume or k in goal for k in kws):
            direction = d
            break
    stage = "校招"
    if "2027" in resume or "大三" in resume or "研一" in resume:
        stage = "实习"
    cities = ["深圳", "北京"]
    for c in ["上海", "杭州", "广州", "成都"]:
        if c in resume + goal:
            cities.insert(0, c)

    state.intent = CareerIntent(direction=direction, stage=stage, target_cities=cities,
                                reasoning=f"关键词推断: {direction}", risk_preference="平衡")
    state.agent_trace.append(f"[JobAnalyzer] direction={direction} stage={stage}")

    # 加载岗位（方向过滤）
    jobs = _load_jobs()
    state.jds = []
    foreign = {'Capgemini','Home Depot','Lockheed Martin','EverCommerce','LinkedIn','Leidos',
               'Meta','Google','Amazon','Apple','Microsoft','OpenAI','Canva','Talkspace'}
    for j in jobs:
        jd = JDProfile(
            title=j.get("title",""), company=j.get("company",""), city=j.get("city",""),
            salary=j.get("salary",""), stage=j.get("stage",""), direction=j.get("direction",""),
            hard_skills=list(j.get("skills",[])), jd_text=j.get("jd_text", j.get("raw_jd_snippet","")),
            source_url=j.get("source_url",""),
        )
        # 过滤外企脏数据
        if jd.company in foreign: continue
        state.jds.append(jd)

    state.agent_trace.append(f"[JobAnalyzer] loaded {len(state.jds)} jobs")
    return state


# ======================================================================
# ResumeReviewer — 证据提取 + 岗位匹配
# ======================================================================

def _node_resume_reviewer(state: AgentState) -> AgentState:
    """提取简历证据 + 匹配每个 JD。"""
    resume = state.resume_text.lower()

    # 证据提取
    skills_map = {
        "python": "python" in resume, "pytorch": "pytorch" in resume,
        "transformer": "transformer" in resume, "rag": "rag" in resume,
        "agent": "agent" in resume or "langgraph" in resume,
        "langchain": "langchain" in resume, "faiss": "faiss" in resume,
        "docker": "docker" in resume, "sql": "sql" in resume,
        "embedding": "embedding" in resume, "微调": "微调" in resume or "finetune" in resume or "sft" in resume,
    }
    evidence = {k: [f"简历包含{k}"] for k, v in skills_map.items() if v}

    state.resume_evidence = ResumeEvidence(
        skill_evidence=evidence,
        gap_areas=[k for k, v in skills_map.items() if not v],
    )
    state.agent_trace.append(f"[ResumeReviewer] evidence: {len(evidence)} skills found, {len(state.resume_evidence.gap_areas)} gaps")

    # 匹配每个 JD
    state.match_results = []
    ev_set = set(evidence.keys())
    for jd in state.jds[:15]:
        jd_skills = {s.lower() for s in jd.hard_skills} if jd.hard_skills else set()
        if not jd_skills:
            continue
        overlap = jd_skills & ev_set
        score = min(int(len(overlap) / max(len(jd_skills), 1) * 100), 100)
        # Agent 方向加分
        if "agent" in str(ev_set) or "langgraph" in str(ev_set):
            score = min(score + 15, 100)

        missing = list(jd_skills - ev_set)[:5]
        apply_action = "暂缓"
        if score >= 75: apply_action = "立即投递"
        elif score >= 60: apply_action = "先优化再投"
        elif score >= 40: apply_action = "冲刺岗位"

        state.match_results.append(MatchResult(
            title=jd.title, company=jd.company,
            match_score=float(score), pass_likelihood=float(score - 10),
            risk_level="低" if score >= 70 else ("中" if score >= 40 else "高"),
            missing_evidence=missing, apply_action=apply_action,
            evidence_based_reasoning=f"匹配度{score}/100，命中{len(overlap)}/{len(jd_skills)}项JD技能",
        ))

    state.match_results.sort(key=lambda m: -m.match_score)
    state.agent_trace.append(f"[ResumeReviewer] matched {len(state.match_results)} jobs")
    return state


# ======================================================================
# ResumeOptimizer — 低分回路：优化简历 + What-if 模拟
# ======================================================================

def _node_resume_optimizer(state: AgentState) -> AgentState:
    """低分匹配 → 生成优化建议 + 反事实模拟。"""
    low_matches = [m for m in state.match_results if m.match_score < 70][:5]
    all_gaps = set()
    for m in low_matches:
        all_gaps.update(m.missing_evidence)

    # What-if 模拟
    what_if = []
    if all_gaps:
        for gap in list(all_gaps)[:3]:
            what_if.append({
                "action": f"补充{gap}相关项目或经验",
                "match_gain": 15 if "agent" in gap.lower() else 10,
                "effort_days": 14 if "agent" in gap.lower() else 7,
                "why": f"当前缺少{gap}，补充后可大幅提升匹配度",
            })

    state.counterfactual = CounterfactualPlan(top3_payoffs=what_if)

    # 优化建议
    rewrites = []
    need_exp = []
    for gap in list(all_gaps)[:5]:
        if gap in state.resume_evidence.skill_evidence if state.resume_evidence else {}:
            rewrites.append(f"将已有{gap}经历改写成JD要求格式")
        else:
            need_exp.append(f"需要先补充{gap}真实项目经历再写入简历")

    state.coach = CoachOutput(can_rewrite=rewrites, need_project_first=need_exp)

    state.agent_trace.append(f"[ResumeOptimizer] {len(what_if)} what-if items, {len(need_exp)} gaps to fill")
    return state


# ======================================================================
# CareerCoach — 生成最终报告
# ======================================================================

def _node_career_coach(state: AgentState) -> AgentState:
    """策略分层 + 今日计划 + 面试准备。"""
    matches = state.match_results
    safe = matches[:2] if len(matches) >= 2 else matches[:1]
    stretch = matches[2:5] if len(matches) >= 5 else matches[2:4]
    skip = matches[5:] if len(matches) > 5 else []

    for m in safe: m.apply_action = "立即投递"
    for m in stretch: m.apply_action = "先优化再投" if m.match_score < 75 else "冲刺岗位"
    for m in skip: m.apply_action = "暂缓"

    state.strategy = StrategyOutput(
        safe_jobs=safe, stretch_jobs=stretch, skip_jobs=skip,
        today_plan=[f"投递 {m.company}-{m.title}" for m in safe[:3]],
        week_plan=["Day 1-2: 投递稳投岗", "Day 3-4: 优化简历+冲刺岗",
                    "Day 5-6: 准备面试", "Day 7: 复盘"],
    )

    # 面试准备
    questions = ["请介绍你的项目经历", "你对这个岗位的理解？"]
    for m in matches[:3]:
        for gap in m.missing_evidence[:2]:
            questions.append(f"你怎么看待{gap}？有相关学习计划吗？")
    state.interview_prep = InterviewPrep(likely_questions=questions[:5])

    state.agent_trace.append(f"[CareerCoach] safe={len(safe)} stretch={len(stretch)} hold={len(skip)}")
    return state


# ======================================================================
# Supervisor — 路由决策
# ======================================================================

def _route(state: AgentState) -> Literal["job_analyzer", "resume_reviewer", "resume_optimizer", "career_coach", "__end__"]:
    if not state.jds or len(state.jds) == 0:
        return "job_analyzer"
    if not state.match_results or len(state.match_results) == 0:
        return "resume_reviewer"
    low_count = sum(1 for m in state.match_results if m.match_score < 50)
    if low_count >= len(state.match_results) * 0.6 and not state.counterfactual:
        return "resume_optimizer"
    if not state.strategy:
        return "career_coach"
    return "__end__"


# ======================================================================
# Build graph
# ======================================================================

def build_graph() -> StateGraph:
    wf = StateGraph(AgentState)

    wf.add_node("job_analyzer", _node_job_analyzer)
    wf.add_node("resume_reviewer", _node_resume_reviewer)
    wf.add_node("resume_optimizer", _node_resume_optimizer)
    wf.add_node("career_coach", _node_career_coach)

    # After each node, go back to supervisor routing
    wf.add_edge("job_analyzer", "resume_reviewer")
    wf.add_edge("resume_reviewer", "resume_optimizer")
    wf.add_edge("resume_optimizer", "career_coach")
    wf.add_edge("career_coach", END)

    wf.set_entry_point("job_analyzer")
    return wf


# ======================================================================
# Public API
# ======================================================================

_graph = None

def run_pipeline(resume: str, goal: str = "") -> "FinalDecisionReport":
    global _graph
    if _graph is None:
        _graph = build_graph().compile()

    state = AgentState(resume_text=resume, user_goal=goal)
    result = _graph.invoke(state)

    # Reconstruct from dict
    final = AgentState(
        resume_text=result.get("resume_text", resume),
        user_goal=result.get("user_goal", goal),
        intent=result.get("intent"),
        jds=result.get("jds", []),
        resume_evidence=result.get("resume_evidence"),
        match_results=result.get("match_results", []),
        counterfactual=result.get("counterfactual"),
        coach=result.get("coach"),
        interview_prep=result.get("interview_prep"),
        strategy=result.get("strategy"),
        agent_trace=result.get("agent_trace", []),
    )

    from final_report import ReportBuilder
    return ReportBuilder().build(final)
