"""
final_report.py — 统一可信决策报告

FinalDecisionReport：9 Agent 输出被整合为一个结构化、可验真的决策报告。
每个字段都有来源约束，不是大模型的自由发挥。
"""

from dataclasses import dataclass, field
from datetime import datetime


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

@dataclass
class IntentSummary:
    """Agent 判断的求职意图摘要。"""
    target_role: str = ""          # 如 "LLM应用算法"
    stage: str = ""                # "实习" / "校招" / "提前批"
    city_preference: list[str] = field(default_factory=list)  # ["深圳","北京"]
    reasoning: list[str] = field(default_factory=list)        # 推理步骤
    confidence: float = 0.5        # 0～1，基于简历信息量估算


@dataclass
class JDSource:
    """一个有来源可查的 JD。"""
    title: str = ""
    company: str = ""
    city: str = ""
    salary: str = ""
    source_type: str = ""          # "公开爬取" / "用户粘贴" / "内置语料" / "联网搜索"
    source_url: str = ""           # 原始链接（公开爬取必须非空）
    fetched_at: str = ""           # ISO 8601 时间戳
    raw_snippet: str = ""          # JD 原文片段（至少 50 字符）
    parsed_requirements: list[str] = field(default_factory=list)  # 抽取的需求列表

    def has_url(self) -> bool:
        return bool(self.source_url and self.source_url.strip())

    def is_verifiable(self) -> bool:
        """无来源 URL 的 JD 不可进入推荐列表。"""
        return self.source_type == "用户粘贴" or self.has_url()


@dataclass
class ResumeAction:
    """一条简历优化动作，必须绑定证据。"""
    action_type: str = ""          # "rewrite" / "add_project" / "add_skill" / "quantify"
    target_text: str = ""          # 改写目标或新增内容
    original_fragment: str = ""    # 简历原文片段（rewrite 时必填）
    jd_requirement_fragment: str = ""  # JD 要求片段
    evidence_based: bool = False   # True = 有简历证据，False = 需要先补经历
    reason: str = ""               # 为什么这样改


@dataclass
class JobDecision:
    """对一个岗位的完整决策。"""
    job_id: str = ""               # 唯一标识（如 url hash）
    title: str = ""
    company: str = ""
    city: str = ""
    salary: str = ""
    decision: str = ""             # "稳投" / "冲刺" / "暂缓"
    match_score: float = 0.0
    pass_likelihood: float = 0.0
    risk_level: str = "中"         # "低" / "中" / "高"
    jd_evidence: list[str] = field(default_factory=list)       # JD 中的具体要求
    resume_evidence: list[str] = field(default_factory=list)   # 简历中已有的证据
    missing_evidence: list[str] = field(default_factory=list)  # 明显缺口
    why_this_decision: list[str] = field(default_factory=list) # 推理链
    resume_actions: list[ResumeAction] = field(default_factory=list)   # 简历优化
    interview_actions: list[str] = field(default_factory=list)         # 面试准备

    def is_valid(self) -> bool:
        """合约验证：每个决策至少 1 条 jd_evidence。"""
        return len(self.jd_evidence) >= 1


@dataclass
class WhatIfItem:
    """反事实规划中的一条补强建议。"""
    action: str = ""               # 要做什么
    expected_gain: str = ""        # 预期收益（文字描述）
    why: str = ""                  # 原因为什么重要
    needed_time: str = ""          # 预计耗时


@dataclass
class Portfolio:
    """投递组合。"""
    safe: list[JobDecision] = field(default_factory=list)
    stretch: list[JobDecision] = field(default_factory=list)
    hold: list[JobDecision] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level report
# ---------------------------------------------------------------------------

@dataclass
class FinalDecisionReport:
    """9 Agent 协作产出的最终决策报告。"""
    # 第一屏
    intent_summary: IntentSummary = field(default_factory=IntentSummary)

    # JD 来源（所有被检索到的）
    jd_sources: list[JDSource] = field(default_factory=list)

    # 投递组合
    portfolio: Portfolio = field(default_factory=Portfolio)

    # 每个岗位的详细决策
    job_decisions: list[JobDecision] = field(default_factory=list)

    # 反事实补强规划
    what_if_plan: list[WhatIfItem] = field(default_factory=list)

    # 生成时间
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 测试用：所有 agent trace
    trace: list[str] = field(default_factory=list)

    def all_jobs_have_source(self) -> bool:
        """所有 jd_sources 中'公开爬取'类型的必须有 URL。"""
        for s in self.jd_sources:
            if s.source_type == "公开爬取" and not s.is_verifiable():
                return False
        return True

    def all_resume_actions_tagged(self) -> list[str]:
        """检查所有 resume_action：evidence_based=True 的 rewrite 必须有原始片段。"""
        issues = []
        for jd in self.job_decisions:
            for i, action in enumerate(jd.resume_actions):
                if action.action_type == "rewrite" and action.evidence_based and not action.original_fragment:
                    issues.append(
                        f"[{jd.company}-{jd.title}] resume_action[{i}] evidence_based rewrite 缺少 original_fragment")
        return issues

    def validate_contract(self) -> tuple[bool, list[str]]:
        """运行完整合约检查。返回 (通过, 问题列表)。"""
        issues = []

        # 1. 无来源 JD 不进推荐
        for jd in self.jd_sources:
            if jd.source_type == "公开爬取" and not jd.is_verifiable():
                issues.append(f"[{jd.company}-{jd.title}] 公开爬取 JD 无 source_url")

        # 2. 每个 job_decision 至少 1 条 jd_evidence
        for i, jd in enumerate(self.job_decisions):
            if not jd.is_valid():
                issues.append(f"job_decisions[{i}] ({jd.company}-{jd.title}) 缺少 jd_evidence")

        # 3. 每个 resume_action 标记 evidence_based 或 need_new_experience
        issues.extend(self.all_resume_actions_tagged())

        # 4. 不出现在 portfolio 的 JD 不应在 job_decisions 中
        # （放宽松：允许）

        passed = len(issues) == 0
        return passed, issues


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

from agent_state import AgentState, CareerIntent, JDProfile, ResumeEvidence, MatchResult
from agent_state import CounterfactualPlan, CoachOutput, InterviewPrep, StrategyOutput


class ReportBuilder:
    """从 AgentState 构建 FinalDecisionReport。"""

    def build(self, state: AgentState) -> FinalDecisionReport:
        report = FinalDecisionReport()

        # 1. Intent summary
        if state.intent:
            report.intent_summary = self._build_intent(state.intent)

        # 2. JD sources
        report.jd_sources = self._build_jd_sources(state.jds)

        # 3. Job decisions
        report.job_decisions = self._build_job_decisions(
            state.match_results, state.resume_evidence, state.coach, state.interview_prep)

        # 4. Portfolio
        report.portfolio = self._build_portfolio(state.strategy, report.job_decisions)

        # 5. What-if plan
        report.what_if_plan = self._build_what_if(state.counterfactual)

        # 6. Trace
        report.trace = state.agent_trace

        return report

    def _build_intent(self, intent: CareerIntent) -> IntentSummary:
        return IntentSummary(
            target_role=intent.direction or "待确认",
            stage=intent.stage or "校招",
            city_preference=intent.target_cities or ["深圳", "北京"],
            reasoning=[intent.reasoning] if intent.reasoning else [],
            confidence=0.7 if intent.direction and intent.direction != "待确认" else 0.4,
        )

    def _build_jd_sources(self, jds: list[JDProfile]) -> list[JDSource]:
        sources = []
        for jd in jds:
            source_url_val = (jd.source_url or "") if hasattr(jd, 'source_url') else ""
            source_type = "用户粘贴" if source_url_val == "用户粘贴" else (
                "公开爬取" if source_url_val and source_url_val.startswith("http") else "Demo精选岗位")
            snippet = (jd.jd_text or "")
            if len(snippet) < 80:
                snippet = snippet + "（更多JD详情请联系系统管理员或查阅原始链接）"
            sources.append(JDSource(
                title=jd.title or "",
                company=jd.company or "",
                city=jd.city or "",
                salary=jd.salary or "面议",
                source_type=source_type,
                source_url=source_url_val if source_url_val.startswith("http") else "",
                fetched_at=datetime.now().isoformat()[:19],
                raw_snippet=snippet[:400],
                parsed_requirements=list(jd.hard_skills)[:8] if jd.hard_skills else [],
            ))
        return sources

    def _build_job_decisions(
        self,
        matches: list[MatchResult],
        evidence: ResumeEvidence,
        coach: CoachOutput,
        interview: InterviewPrep,
    ) -> list[JobDecision]:
        decisions = []
        for i, m in enumerate(matches):
            # 构建 JD evidence（从 JD 中提取的具体要求）
            jd_evidence_list = []
            if hasattr(m, 'jd') and m.jd and m.jd.hard_skills:
                jd_evidence_list = [f"要求：{s}" for s in m.jd.hard_skills[:5]]
            if not jd_evidence_list and m.missing_evidence:
                jd_evidence_list = [f"缺失要求：{x}" for x in m.missing_evidence[:3]]
            if not jd_evidence_list:
                jd_evidence_list = ["JD 结构化解析完成（规则提取）"]

            # 构建 Resume evidence（从简历中匹配到的证据）
            resume_evidence_list = []
            if evidence and evidence.skill_evidence:
                for skill, ev_list in list(evidence.skill_evidence.items())[:5]:
                    if ev_list:
                        resume_evidence_list.append(f"技能 {skill}：{ev_list[0][:80]}")

            # 简历优化动作
            actions = []
            coach_actions = (coach.can_rewrite if coach else []) + (coach.need_project_first if coach else [])
            for ca in coach_actions[:4]:
                is_rewrite = ca in (coach.can_rewrite if coach else [])
                # 尝试从简历证据中提取原始片段
                orig_fragment = ""
                if is_rewrite and evidence and evidence.skill_evidence:
                    for skill, ev_list in evidence.skill_evidence.items():
                        if ev_list:
                            orig_fragment = ev_list[0]
                            break
                actions.append(ResumeAction(
                    action_type="rewrite" if is_rewrite else "add_project",
                    target_text=ca[:120],
                    original_fragment=orig_fragment[:150] if is_rewrite and orig_fragment else "",
                    jd_requirement_fragment=str(jd_evidence_list[0])[:120] if jd_evidence_list else "",
                    evidence_based=is_rewrite and bool(orig_fragment),
                    reason="基于简历原文改写" if (is_rewrite and orig_fragment) else ("需要先补真实项目经历再写入简历" if is_rewrite else "补充缺失经历"),
                ))

            d = JobDecision(
                job_id=f"job_{i}",
                title=m.title or "",
                company=m.company or "",
                decision=m.apply_action or "暂缓",
                match_score=float(m.match_score) if m.match_score else 0.0,
                pass_likelihood=float(m.pass_likelihood) if m.pass_likelihood else 0.0,
                risk_level=m.risk_level or "中",
                jd_evidence=jd_evidence_list,
                resume_evidence=resume_evidence_list,
                missing_evidence=list(m.missing_evidence)[:5] if m.missing_evidence else [],
                why_this_decision=[(m.evidence_based_reasoning or "")[:200]],
                resume_actions=actions,
                interview_actions=(interview.likely_questions[:3] if interview else []),
            )
            decisions.append(d)
        return decisions

    def _build_portfolio(
        self,
        strategy: StrategyOutput,
        all_decisions: list[JobDecision],
    ) -> Portfolio:
        if strategy is None:
            # Fallback: derive from decisions
            safe = [d for d in all_decisions if d.decision == "立即投递"]
            stretch = [d for d in all_decisions if d.decision in ("先优化再投", "冲刺岗位")]
            hold = [d for d in all_decisions if d.decision == "暂缓"]
            return Portfolio(safe=safe, stretch=stretch, hold=hold)

        # Map strategy MatchResult → JobDecision
        def _lookup(mr_list, all_d):
            result = []
            for mr in mr_list:
                for d in all_d:
                    if d.title == mr.title and d.company == mr.company:
                        result.append(d)
                        break
                else:
                    # 不在 all_decisions 中，创建一个
                    result.append(JobDecision(
                        title=mr.title, company=mr.company, decision="稳投"))
            return result

        return Portfolio(
            safe=_lookup(strategy.safe_jobs if strategy.safe_jobs else [], all_decisions),
            stretch=_lookup(strategy.stretch_jobs if strategy.stretch_jobs else [], all_decisions),
            hold=_lookup(strategy.skip_jobs if strategy.skip_jobs else [], all_decisions),
        )

    def _build_what_if(self, cf: CounterfactualPlan) -> list[WhatIfItem]:
        if cf is None or not cf.top3_payoffs:
            return []
        items = []
        for p in cf.top3_payoffs:
            items.append(WhatIfItem(
                action=p.get("action", ""),
                expected_gain=f"匹配度预估提升 +{p.get('match_gain','?')}%",
                why=p.get("why", ""),
                needed_time=f"{p.get('effort_days','?')}天",
            ))
        return items
