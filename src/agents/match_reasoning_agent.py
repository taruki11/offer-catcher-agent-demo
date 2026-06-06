"""
Match Reasoning Agent — 面试官式匹配判断，不是 cosine similarity。

核心理念：像面试官一样阅读 JD 和简历，给出有证据的匹配判断。
"""

import json
from agent_state import MatchResult, JDProfile, ResumeEvidence

_PROMPT = """你是一位资深技术面试官，正在评估候选人是否适合某个岗位。

请根据 JD 要求和候选人简历证据，给出匹配判断。像面试官一样推理，不要做简单的关键词匹配。

输出 JSON：
{
  "match_score": 75,
  "pass_likelihood": 60,
  "risk_level": "低 | 中 | 高",
  "evidence_based_reasoning": "该候选人匹配度75/100。优势：Python/PyTorch经验丰富，有Transformer项目。不足：缺少LangGraph经验，Agent方向项目偏少。通过率预估60%，主要风险在Agent框架经验不足。",
  "missing_evidence": ["LangGraph多Agent项目", "Agent评测经验"],
  "apply_action": "立即投递 | 先优化再投 | 冲刺岗位 | 暂缓"
}

评分标准：
- match_score (0-100)：综合匹配度
- pass_likelihood (0-100)：预估通过初筛的概率
- risk_level：低(>=70%通过) / 中(40-70%) / 高(<40%)
- apply_action：match_score>=75且risk低 → 立即投递；match_score>=60 → 先优化再投；growth潜力大 → 冲刺岗位；否则暂缓

JD 信息：
岗位：{title} @ {company} · {city}
硬技能要求：{hard_skills}
软技能要求：{soft_skills}
学历要求：{education}
加分项：{bonus}
隐含要求：{hidden}

候选人简历证据：
技能证据：{skill_evidence}
项目证据：{project_evidence}
量化指标：{metrics}
LLM经验：{llm_evidence}
Agent经验：{agent_evidence}"""


class MatchReasoningAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def evaluate(self, jd: JDProfile, evidence: ResumeEvidence) -> MatchResult:
        if self.llm and self.llm.available:
            prompt = _PROMPT
            prompt = prompt.replace("{title}", jd.title)
            prompt = prompt.replace("{company}", jd.company)
            prompt = prompt.replace("{city}", jd.city)
            prompt = prompt.replace("{hard_skills}", ", ".join(jd.hard_skills))
            prompt = prompt.replace("{soft_skills}", ", ".join(jd.soft_skills))
            prompt = prompt.replace("{education}", jd.education)
            prompt = prompt.replace("{bonus}", ", ".join(jd.bonus_points))
            prompt = prompt.replace("{hidden}", ", ".join(jd.hidden_requirements))
            prompt = prompt.replace("{skill_evidence}", str(evidence.skill_evidence)[:500])
            prompt = prompt.replace("{project_evidence}", str(evidence.project_evidence)[:500])
            prompt = prompt.replace("{metrics}", ", ".join(evidence.metrics_evidence))
            prompt = prompt.replace("{llm_evidence}", ", ".join(evidence.llm_evidence))
            prompt = prompt.replace("{agent_evidence}", ", ".join(evidence.agent_evidence))
            try:
                resp = self.llm.chat(prompt, temperature=0.3, max_tokens=800)
                data = self._parse_json(resp)
                return MatchResult(
                    title=jd.title, company=jd.company,
                    match_score=data.get("match_score", 50),
                    pass_likelihood=data.get("pass_likelihood", 50),
                    risk_level=data.get("risk_level", "中"),
                    evidence_based_reasoning=data.get("evidence_based_reasoning", ""),
                    missing_evidence=data.get("missing_evidence", []),
                    apply_action=data.get("apply_action", "先优化再投"),
                )
            except Exception:
                pass
        return self._fallback(jd, evidence)

    def _fallback(self, jd: JDProfile, evidence: ResumeEvidence) -> MatchResult:
        """规则版匹配"""
        ev_skills = set(evidence.skill_evidence.keys())
        all_skills_lower = {s.lower() for s in ev_skills}
        jd_skills_lower = {s.lower() for s in jd.hard_skills}

        if not jd_skills_lower:
            return MatchResult(title=jd.title, company=jd.company, match_score=50, apply_action="先优化再投")

        overlap = jd_skills_lower & all_skills_lower
        match = int(len(overlap) / len(jd_skills_lower) * 100)

        # Agent 方向加分
        if "agent" in str(evidence.agent_evidence).lower():
            match = min(match + 15, 100)

        action = "暂缓"
        if match >= 75:
            action = "立即投递"
        elif match >= 60:
            action = "先优化再投"
        elif match >= 40:
            action = "冲刺岗位"

        return MatchResult(
            title=jd.title, company=jd.company,
            match_score=match,
            pass_likelihood=match - 10,
            risk_level="低" if match >= 70 else ("中" if match >= 40 else "高"),
            missing_evidence=list(jd_skills_lower - all_skills_lower),
            apply_action=action,
        )

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
