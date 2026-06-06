"""
Agent State — shared state schema for LangGraph workflow.

All agents read/write this typed dict.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CareerIntent:
    direction: str           # 大模型算法 / LLM应用算法 / Agent算法 / 推荐转大模型 / 后端转AI
    stage: str               # 实习 / 校招 / 提前批
    target_cities: list[str] # ["深圳", "北京"]
    salary_min: Optional[int] = None
    risk_preference: str = "平衡"  # 稳妥 / 平衡 / 冲刺
    reasoning: str = ""      # Agent 的判断理由


@dataclass
class JDProfile:
    title: str
    company: str
    city: str
    salary: str
    source_url: str = ""
    jd_text: str = ""
    hard_skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    education: str = ""
    bonus_points: list[str] = field(default_factory=list)
    hidden_requirements: list[str] = field(default_factory=list)
    direction: str = ""
    stage: str = ""


@dataclass
class ResumeEvidence:
    skill_evidence: dict = field(default_factory=dict)  # skill → [evidence_fragment, ...]
    project_evidence: dict = field(default_factory=dict)  # project → [evidence_fragment, ...]
    metrics_evidence: list[str] = field(default_factory=list)
    llm_evidence: list[str] = field(default_factory=list)
    agent_evidence: list[str] = field(default_factory=list)
    gap_areas: list[str] = field(default_factory=list)  # 明显缺失的方向


@dataclass
class MatchResult:
    title: str = ""
    company: str = ""
    match_score: float = 0.0
    pass_likelihood: float = 0.0
    risk_level: str = "中"
    evidence_based_reasoning: str = ""
    missing_evidence: list[str] = field(default_factory=list)
    apply_action: str = "暂缓"


@dataclass
class CounterfactualPlan:
    what_if_items: list[dict] = field(default_factory=list)
    top3_payoffs: list[dict] = field(default_factory=list)


@dataclass
class CoachOutput:
    can_rewrite: list[str] = field(default_factory=list)
    need_project_first: list[str] = field(default_factory=list)
    dont_fabricate: list[str] = field(default_factory=list)
    optimized_resume_fragments: dict = field(default_factory=dict)


@dataclass
class InterviewPrep:
    likely_questions: list[str] = field(default_factory=list)
    prep_plan_7day: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)


@dataclass
class StrategyOutput:
    safe_jobs: list[MatchResult] = field(default_factory=list)
    stretch_jobs: list[MatchResult] = field(default_factory=list)
    skip_jobs: list[MatchResult] = field(default_factory=list)
    today_plan: list[str] = field(default_factory=list)
    week_plan: list[str] = field(default_factory=list)


@dataclass
class AgentState:
    """Full state graph for LangGraph workflow."""
    resume_text: str = ""
    user_goal: str = ""
    intent: Optional[CareerIntent] = None
    jds: list[JDProfile] = field(default_factory=list)
    resume_evidence: Optional[ResumeEvidence] = None
    match_results: list[MatchResult] = field(default_factory=list)
    counterfactual: Optional[CounterfactualPlan] = None
    coach: Optional[CoachOutput] = None
    interview_prep: Optional[InterviewPrep] = None
    strategy: Optional[StrategyOutput] = None
    error: str = ""
    agent_trace: list[str] = field(default_factory=list)
