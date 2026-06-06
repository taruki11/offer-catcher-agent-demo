"""
Strategy Planner Agent — 投递策略、优先级排序、7天计划。

输出：稳投/冲刺/暂缓 + 今日计划 + 7天计划
"""

import json
from agent_state import StrategyOutput, MatchResult

_PROMPT = """你是求职策略顾问。给定候选人的岗位匹配结果，输出投递策略。

输出 JSON：
{
  "safe_jobs": [{"title": "xx", "company": "yy", "reason": "匹配度85，风险低"}],
  "stretch_jobs": [{"title": "zz", "company": "ww", "reason": "Growth潜力大，值得冲刺"}],
  "skip_jobs": [{"title": "aa", "company": "bb", "reason": "匹配度低，投入产出比差"}],
  "today_plan": ["投递腾讯-大模型算法", "投递字节-推荐算法"],
  "week_plan": ["Day1: 投递稳投岗位Top3", "Day2: 准备面试常见问题", "Day3-4: 投递冲刺岗位", "Day5: 跟进已投岗位", "Day6: 优化简历", "Day7: 复盘调整策略"]
}

分类规则：
- safe_jobs：match_score >= 75 且 risk_level="低"
- stretch_jobs：match_score < 75 但 growth 潜力大或方向稀缺
- skip_jobs：match_score < 50 且 risk_level="高"

匹配结果：
{matches}"""


class StrategyPlannerAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def plan(self, matches: list[MatchResult]) -> StrategyOutput:
        if self.llm and self.llm.available:
            matches_str = "\n".join(
                f"- {m.title}@{m.company}: match={m.match_score}, pass={m.pass_likelihood}, "
                f"risk={m.risk_level}, action={m.apply_action}"
                for m in matches[:10]
            )
            try:
                resp = self.llm.chat(_PROMPT.replace("{matches}", matches_str), temperature=0.4, max_tokens=800)
                data = self._parse_json(resp)
                # Build MatchResult from dicts
                safe = [MatchResult(title=m.get("title", ""), company=m.get("company", "")) for m in data.get("safe_jobs", [])]
                stretch = [MatchResult(title=m.get("title", ""), company=m.get("company", "")) for m in data.get("stretch_jobs", [])]
                skip = [MatchResult(title=m.get("title", ""), company=m.get("company", "")) for m in data.get("skip_jobs", [])]
                return StrategyOutput(
                    safe_jobs=safe, stretch_jobs=stretch, skip_jobs=skip,
                    today_plan=data.get("today_plan", []),
                    week_plan=data.get("week_plan", []),
                )
            except Exception:
                pass
        return self._fallback(matches)

    def _fallback(self, matches: list[MatchResult]) -> StrategyOutput:
        """策略分层：Top2 稳投，Top3-5 冲刺，其余暂缓。"""
        sorted_matches = sorted(matches, key=lambda m: -m.match_score)
        safe = sorted_matches[:2] if len(sorted_matches) >= 2 else sorted_matches[:1]
        stretch = sorted_matches[2:5] if len(sorted_matches) >= 5 else sorted_matches[2:4]
        skip = sorted_matches[5:] if len(sorted_matches) > 5 else []

        # 更新 apply_action 字段以匹配策略
        for m in safe:
            m.apply_action = "立即投递"
        for m in stretch:
            m.apply_action = "先优化再投" if m.match_score < 75 else "冲刺岗位"
        for m in skip:
            m.apply_action = "暂缓"

        today = [f"投递 {m.company}-{m.title}" for m in safe[:3]]
        week = [
            "Day 1-2: 投递稳投岗位",
            "Day 3-4: 投递冲刺岗位，准备笔试",
            "Day 5-6: 跟进、优化简历",
            "Day 7: 复盘、调整策略",
        ]
        return StrategyOutput(safe_jobs=safe, stretch_jobs=stretch, skip_jobs=skip,
                              today_plan=today, week_plan=week)

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
