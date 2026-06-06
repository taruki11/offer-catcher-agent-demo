"""
Counterfactual Planning Agent — "如果补X，匹配度会提高多少？"

核心亮点：模拟补强效果，给出量化预估。
"""

import json
from agent_state import CounterfactualPlan, MatchResult, ResumeEvidence

_PROMPT = """你是一位职业规划师和技术面试官。给定候选人的当前简历证据和目标岗位匹配结果，请进行反事实模拟：

如果候选人补充以下任何一个方向的项目/技能/经历，匹配度会提高多少？为什么？

输出 JSON：
{
  "what_if_items": [
    {"action": "补LangGraph多Agent项目", "match_gain": 18, "confidence": "高", "reason": "Agent算法岗位明确要求Agent框架经验，补LangGraph项目直接命中核心要求"},
    {"action": "参与开源Agent项目(如AutoGPT/CrewAI)", "match_gain": 12, "confidence": "中", "reason": "开源贡献能体现Agent实战能力"},
    {"action": "刷Agent方向论文并写技术博客", "match_gain": 8, "confidence": "低", "reason": "论文能提升理论深度，但实战经验更重要"}
  ],
  "top3_payoffs": [
    {"action": "补LangGraph多Agent项目", "match_gain": 18, "effort_days": 14, "why": "Agent岗位最需要的核心能力"},
    {"action": "参与开源Agent项目", "match_gain": 12, "effort_days": 21, "why": "实战背书"},
    {"action": "把推荐项目改写成LLM推荐", "match_gain": 10, "effort_days": 5, "why": "成本最低的快速提升"}
  ]
}

规则：
- match_gain：0-30 的整数，预估匹配度提升百分比
- confidence：高（确定能提升）/ 中（可能提升）/ 低（不确定）
- effort_days：预估需要的天数

当前简历证据：
技能：{skills}
缺口：{gaps}

目标岗位匹配结果：
{matches}"""


class CounterfactualPlanningAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def plan(self, evidence: ResumeEvidence, matches: list[MatchResult]) -> CounterfactualPlan:
        skills_str = str(list(evidence.skill_evidence.keys()))
        gaps_str = str(evidence.gap_areas)

        # 收集所有缺口
        all_gaps = list(evidence.gap_areas)
        for m in matches:
            all_gaps.extend(m.missing_evidence)
        all_gaps = list(set(all_gaps))[:8]

        matches_str = "\n".join(
            f"- {m.title}@{m.company}: match={m.match_score}, missing={m.missing_evidence}"
            for m in matches[:5]
        )

        if self.llm and self.llm.available:
            prompt = _PROMPT.replace("{skills}", skills_str).replace("{gaps}", gaps_str).replace("{matches}", matches_str)
            try:
                resp = self.llm.chat(prompt, temperature=0.5, max_tokens=1000)
                data = self._parse_json(resp)
                return CounterfactualPlan(
                    what_if_items=data.get("what_if_items", []),
                    top3_payoffs=data.get("top3_payoffs", []),
                )
            except Exception:
                pass
        return self._fallback(evidence, all_gaps)

    def _fallback(self, evidence: ResumeEvidence, gaps: list[str]) -> CounterfactualPlan:
        items = []
        for gap in gaps[:5]:
            items.append({
                "action": f"补{gap}相关项目",
                "match_gain": 10,
                "confidence": "中",
                "reason": f"当前缺少{gap}经验，补充后可直接提升匹配度",
            })
        top3 = [
            {"action": "完成一个Agent多智能体项目", "match_gain": 15, "effort_days": 10, "why": "Agent方向最核心能力"},
            {"action": "补充量化指标到简历", "match_gain": 10, "effort_days": 3, "why": "量化指标提升简历通过率"},
            {"action": "学习LangGraph并做Demo", "match_gain": 12, "effort_days": 7, "why": "Agent框架经验需求大"},
        ]
        return CounterfactualPlan(what_if_items=items, top3_payoffs=top3)

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
