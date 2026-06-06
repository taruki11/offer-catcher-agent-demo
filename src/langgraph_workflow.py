"""
langgraph_workflow.py — 基于 LangGraph StateGraph 的多 Agent 求职决策工作流。

9 个 Agent 通过有向无环图编排，共享 AgentState，支持条件路由。
"""

from pathlib import Path
import json

from langgraph.graph import StateGraph, END
from agent_state import AgentState
from agents import (
    CareerIntentAgent,
    JobScoutAgent,
    JDAnalystAgent,
    ResumeEvidenceAgent,
    MatchReasoningAgent,
    CounterfactualPlanningAgent,
    ResumeCoachAgent,
    InterviewCoachAgent,
    StrategyPlannerAgent,
)


# ============================================================================
# Node functions — 每个 Agent 包装为一个 LangGraph node
# ============================================================================

def _node_career_intent(state: AgentState) -> AgentState:
    agent = CareerIntentAgent(llm_client=None)
    state.intent = agent.run(state.resume_text, state.user_goal)
    state.agent_trace.append(f"[CareerIntent] direction={state.intent.direction} stage={state.intent.stage}")
    return state


def _node_job_scout(state: AgentState) -> AgentState:
    corpus = _load_local_corpus()
    scout = JobScoutAgent()
    state.jds = scout.scout(state.intent, local_corpus=corpus)
    state.agent_trace.append(f"[JobScout] found {len(state.jds)} jobs")
    return state


def _node_jd_analyst(state: AgentState) -> AgentState:
    analyst = JDAnalystAgent()
    for i, jd in enumerate(state.jds):
        if not jd.hard_skills and jd.jd_text:
            try:
                analyzed = analyst.analyze(jd.jd_text, {
                    "title": jd.title, "company": jd.company,
                    "city": jd.city, "salary": jd.salary,
                    "source_url": jd.source_url,
                })
                state.jds[i] = analyzed
            except Exception:
                pass
    state.agent_trace.append(f"[JDAnalyst] analyzed {len(state.jds)} JDs")
    return state


def _node_resume_evidence(state: AgentState) -> AgentState:
    agent = ResumeEvidenceAgent()
    direction = state.intent.direction if state.intent else ""
    state.resume_evidence = agent.run(state.resume_text, direction)
    ev = state.resume_evidence
    state.agent_trace.append(f"[Evidence] skills={len(ev.skill_evidence)} gaps={len(ev.gap_areas)}")
    return state


def _node_match_reasoning(state: AgentState) -> AgentState:
    agent = MatchReasoningAgent()
    state.match_results = []
    for jd in state.jds[:15]:
        result = agent.evaluate(jd, state.resume_evidence)
        state.match_results.append(result)
    state.match_results.sort(key=lambda x: -x.match_score)
    state.agent_trace.append(f"[Match] {len(state.match_results)} matched")
    return state


def _node_counterfactual(state: AgentState) -> AgentState:
    agent = CounterfactualPlanningAgent()
    top_matches = state.match_results[:5] if len(state.match_results) >= 5 else state.match_results
    state.counterfactual = agent.plan(state.resume_evidence, top_matches)
    cf = state.counterfactual
    state.agent_trace.append(f"[Counterfactual] {len(cf.top3_payoffs)} suggestions")
    return state


def _node_resume_coach(state: AgentState) -> AgentState:
    agent = ResumeCoachAgent()
    target = state.jds[0] if state.jds else None
    state.coach = agent.coach(state.resume_text, state.resume_evidence, target)
    c = state.coach
    state.agent_trace.append(f"[ResumeCoach] rewrite={len(c.can_rewrite)} need_first={len(c.need_project_first)}")
    return state


def _node_interview_coach(state: AgentState) -> AgentState:
    agent = InterviewCoachAgent()
    top_matches = state.match_results[:3]
    state.interview_prep = agent.prepare(top_matches, state.resume_evidence)
    state.agent_trace.append(f"[Interview] {len(state.interview_prep.likely_questions)} Qs")
    return state


def _node_strategy_planner(state: AgentState) -> AgentState:
    agent = StrategyPlannerAgent()
    state.strategy = agent.plan(state.match_results)
    s = state.strategy
    state.agent_trace.append(f"[Strategy] safe={len(s.safe_jobs)} stretch={len(s.stretch_jobs)} skip={len(s.skip_jobs)}")
    return state


# ============================================================================
# Conditional routing
# ============================================================================

def _route_after_job_scout(state: AgentState) -> str:
    """如果 JD 不足 3 个，仍继续（demo 稳定性优先）。"""
    return "jd_analyst"


def _route_after_match(state: AgentState) -> str:
    """如果所有匹配都低分，直接走 strategy（跳过 counterfactual + coach）。"""
    if state.match_results and all(m.match_score < 30 for m in state.match_results[:5]):
        state.agent_trace.append("[Route] all low scores → skip to strategy")
        return "strategy_planner"
    return "counterfactual"


# ============================================================================
# Graph builder
# ============================================================================

def build_offer_catcher_graph() -> StateGraph:
    """构建 LangGraph StateGraph。"""
    workflow = StateGraph(AgentState)

    # 添加 9 个节点
    workflow.add_node("career_intent", _node_career_intent)
    workflow.add_node("job_scout", _node_job_scout)
    workflow.add_node("jd_analyst", _node_jd_analyst)
    workflow.add_node("resume_evidence", _node_resume_evidence)
    workflow.add_node("match_reasoning", _node_match_reasoning)
    workflow.add_node("counterfactual", _node_counterfactual)
    workflow.add_node("resume_coach", _node_resume_coach)
    workflow.add_node("interview_coach", _node_interview_coach)
    workflow.add_node("strategy_planner", _node_strategy_planner)

    # 主顺序边
    workflow.set_entry_point("career_intent")
    workflow.add_edge("career_intent", "job_scout")
    workflow.add_conditional_edges("job_scout", _route_after_job_scout, {"jd_analyst": "jd_analyst"})
    workflow.add_edge("jd_analyst", "resume_evidence")
    workflow.add_edge("resume_evidence", "match_reasoning")
    workflow.add_conditional_edges("match_reasoning", _route_after_match, {
        "counterfactual": "counterfactual",
        "strategy_planner": "strategy_planner",
    })
    workflow.add_edge("counterfactual", "resume_coach")
    workflow.add_edge("resume_coach", "interview_coach")
    workflow.add_edge("interview_coach", "strategy_planner")
    workflow.add_edge("strategy_planner", END)

    return workflow


# ============================================================================
# Public API
# ============================================================================

_graph = None  # 缓存编译后的图


def run_full_pipeline(resume: str, goal: str = "", use_online: bool = False):
    """
    一站式执行：编译 LangGraph 图，运行 9 Agent 工作流，返回 FinalDecisionReport。
    """
    global _graph
    if _graph is None:
        _graph = build_offer_catcher_graph().compile()

    # 构建初始状态
    state = AgentState(resume_text=resume, user_goal=goal)

    # 如果启用 LLM，注入 client（当前 demo 默认规则版）
    # 注意：这里 LLM client 暂不通过 graph 注入，agent 内部自行 fallback

    # 执行图（返回 dict）
    result_dict = _graph.invoke(state)

    # 从 dict 重建 AgentState（LangGraph 返回 TypedDict）
    final_state = AgentState(
        resume_text=result_dict.get("resume_text", resume),
        user_goal=result_dict.get("user_goal", goal),
        intent=result_dict.get("intent"),
        jds=result_dict.get("jds", []),
        resume_evidence=result_dict.get("resume_evidence"),
        match_results=result_dict.get("match_results", []),
        counterfactual=result_dict.get("counterfactual"),
        coach=result_dict.get("coach"),
        interview_prep=result_dict.get("interview_prep"),
        strategy=result_dict.get("strategy"),
        agent_trace=result_dict.get("agent_trace", []),
    )

    # 构建报告
    from final_report import ReportBuilder
    builder = ReportBuilder()
    return builder.build(final_state)


def _load_local_corpus() -> list[dict]:
    """加载本地岗位缓存。"""
    root = Path(__file__).resolve().parent.parent
    for fname in ("jobs_corpus.json", "jobs_merged.json", "jobs.json"):
        path = root / "data" / fname
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return []
