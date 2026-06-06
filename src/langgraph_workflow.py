"""
LangGraph Workflow — 多 Agent 求职决策流水线。

状态流转：
ResumeInput → CareerIntent → JobScout → JDAnalyst → ResumeEvidence
→ MatchReasoning → CounterfactualPlanning → ResumeCoach → InterviewCoach → StrategyPlanner → FinalReport
"""

from agent_state import AgentState, CareerIntent, ResumeEvidence, MatchResult, StrategyOutput
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

from pathlib import Path
import json


class OfferCatcherWorkflow:
    """主工作流 — 9 Agent 协作完成求职决策。"""

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.trace: list[str] = []

    def run(self, resume: str, goal: str = "",
            user_jds: list[dict] | None = None,
            local_corpus: list[dict] | None = None) -> AgentState:
        """
        执行完整多 Agent 流水线。

        Args:
            resume: 简历文本
            goal: 用户一句话目标
            user_jds: 用户粘贴的 JD
            local_corpus: 本地岗位缓存

        Returns:
            AgentState: 包含所有 Agent 的输出
        """
        state = AgentState(resume_text=resume, user_goal=goal)

        # Step 1: Career Intent
        self._log("CareerIntentAgent 开始...")
        state.intent = CareerIntentAgent(self.llm).run(resume, goal)
        state.agent_trace.append(f"[CareerIntent] direction={state.intent.direction} stage={state.intent.stage}")
        self._log(f"  方向={state.intent.direction}, 阶段={state.intent.stage}")

        # Step 2: Job Scout
        self._log("JobScoutAgent 搜索岗位...")
        scout = JobScoutAgent(self.llm)
        state.jds = scout.scout(state.intent, user_jds, local_corpus)
        state.agent_trace.append(f"[JobScout] 找到{len(state.jds)}个岗位")
        self._log(f"  找到{len(state.jds)}个岗位")

        # Step 3: JD Analyst
        self._log("JDAnalystAgent 分析JD...")
        analyst = JDAnalystAgent(self.llm)
        for i, jd in enumerate(state.jds):
            if not jd.hard_skills and jd.jd_text:
                try:
                    analyzed = analyst.analyze(jd.jd_text, {
                        "title": jd.title, "company": jd.company,
                        "city": jd.city, "salary": jd.salary,
                        "source_url": jd.source_url,
                    })
                    state.jds[i] = analyzed
                except Exception as e:
                    state.agent_trace.append(f"[JDAnalyst] #{i} 失败: {e}")
        state.agent_trace.append(f"[JDAnalyst] 完成{len(state.jds)}个JD分析")

        # Step 4: Resume Evidence
        self._log("ResumeEvidenceAgent 提取证据...")
        evidence_agent = ResumeEvidenceAgent(self.llm)
        state.resume_evidence = evidence_agent.run(resume, state.intent.direction)
        state.agent_trace.append(f"[ResumeEvidence] 技能={len(state.resume_evidence.skill_evidence)} 缺口={len(state.resume_evidence.gap_areas)}")

        # Step 5: Match Reasoning
        self._log("MatchReasoningAgent 匹配推理...")
        matcher = MatchReasoningAgent(self.llm)
        state.match_results = []
        for jd in state.jds[:15]:  # 最多匹配15个
            result = matcher.evaluate(jd, state.resume_evidence)
            state.match_results.append(result)
        state.match_results.sort(key=lambda x: -x.match_score)
        state.agent_trace.append(f"[MatchReasoning] 完成{len(state.match_results)}个岗位匹配")

        # Step 6: Counterfactual Planning
        self._log("CounterfactualPlanningAgent 反事实规划...")
        cf_agent = CounterfactualPlanningAgent(self.llm)
        state.counterfactual = cf_agent.plan(state.resume_evidence, state.match_results[:5])
        state.agent_trace.append(f"[Counterfactual] {len(state.counterfactual.top3_payoffs)}个补强建议")

        # Step 7: Resume Coach
        self._log("ResumeCoachAgent 简历优化...")
        coach_agent = ResumeCoachAgent(self.llm)
        target_jd = state.jds[0] if state.jds else None
        state.coach = coach_agent.coach(resume, state.resume_evidence, target_jd)
        state.agent_trace.append(f"[ResumeCoach] 可改写={len(state.coach.can_rewrite)} 需补={len(state.coach.need_project_first)}")

        # Step 8: Interview Coach
        self._log("InterviewCoachAgent 面试准备...")
        interview_agent = InterviewCoachAgent(self.llm)
        state.interview_prep = interview_agent.prepare(state.match_results[:3], state.resume_evidence)
        state.agent_trace.append(f"[InterviewCoach] {len(state.interview_prep.likely_questions)}个问题 {len(state.interview_prep.prep_plan_7day)}天计划")

        # Step 9: Strategy Planner
        self._log("StrategyPlannerAgent 投递策略...")
        strategy_agent = StrategyPlannerAgent(self.llm)
        state.strategy = strategy_agent.plan(state.match_results)
        state.agent_trace.append(f"[Strategy] 稳投={len(state.strategy.safe_jobs)} 冲刺={len(state.strategy.stretch_jobs)}")

        self._log("✓ 全部 Agent 执行完毕")
        return state

    def _log(self, msg: str):
        self.trace.append(msg)

    def get_trace(self) -> str:
        return "\n".join(self.trace)

    def build_report(self, state: AgentState):
        """从 AgentState 构建 FinalDecisionReport。"""
        from final_report import ReportBuilder
        builder = ReportBuilder()
        return builder.build(state)


def run_full_pipeline(resume: str, goal: str = "", use_online: bool = False):
    """
    一站式执行：跑完 9 Agent 工作流，返回 FinalDecisionReport。
    
    Args:
        resume: 简历文本
        goal: 用户目标
        use_online: 是否启用 LLM API（默认规则版）

    Returns:
        FinalDecisionReport：统一的决策报告
    """
    from llm_client import LLMClient

    llm = LLMClient() if use_online else None
    workflow = OfferCatcherWorkflow(llm_client=llm)
    corpus = _load_local_corpus()
    state = workflow.run(resume, goal, local_corpus=corpus)
    return workflow.build_report(state)


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
