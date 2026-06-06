"""
Interview Coach Agent — 生成面试准备包。

输出：高频问题、7天准备计划、重点复习方向。
"""

import json
from agent_state import InterviewPrep, MatchResult, ResumeEvidence

_PROMPT = """你是面试辅导教练。给定候选人匹配的目标岗位和简历证据，生成面试准备包。

输出 JSON：
{
  "likely_questions": [
    "请介绍你的Agent项目，里面用了什么架构？",
    "Transformer的attention机制和现在LLM的attention有什么不同？",
    "RAG系统中怎么解决检索质量不稳定的问题？"
  ],
  "prep_plan_7day": [
    "Day1: 复习Transformer/Attention基础，准备技术深挖问题",
    "Day2: 梳理Agent项目，准备STAR回答框架",
    "Day3: 刷LeetCode medium 2-3题（算法岗必考）",
    "Day4: 模拟面试：Agent方向技术面",
    "Day5: 准备反问环节：问团队技术栈、业务方向",
    "Day6: 复习简历中每个项目，确保能讲清楚挑战和成果",
    "Day7: 轻复习+调整心态"
  ],
  "focus_areas": ["Agent架构设计", "RAG优化", "Transformer细节"]
}

规则：
- likely_questions：根据 JD 技能要求和简历缺口生成最可能被问的技术问题
- prep_plan_7day：7天准备计划，每天1-2个重点
- focus_areas：3-5个最需要重点复习的方向

目标岗位：
{target_jobs}

简历证据：
{evidence}

缺口：
{gaps}"""


class InterviewCoachAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def prepare(self, matches: list[MatchResult], evidence: ResumeEvidence) -> InterviewPrep:
        if self.llm and self.llm.available:
            jobs_str = "\n".join(
                f"- {m.title}@{m.company}: skills missing={m.missing_evidence}"
                for m in matches[:3]
            )
            prompt = _PROMPT.replace("{target_jobs}", jobs_str).replace("{evidence}", str(list(evidence.skill_evidence.keys()))).replace("{gaps}", str(evidence.gap_areas))
            try:
                resp = self.llm.chat(prompt, temperature=0.5, max_tokens=800)
                data = self._parse_json(resp)
                return InterviewPrep(
                    likely_questions=data.get("likely_questions", []),
                    prep_plan_7day=data.get("prep_plan_7day", []),
                    focus_areas=data.get("focus_areas", []),
                )
            except Exception:
                pass
        return self._fallback(matches, evidence)

    def _fallback(self, matches: list[MatchResult], evidence: ResumeEvidence) -> InterviewPrep:
        questions = ["请详细介绍你的项目经历", "你对这个岗位的理解是什么？"]
        skills = list(evidence.skill_evidence.keys())
        for s in skills[:3]:
            questions.append(f"请说说你在{s}方面的经验和理解")
        for gap in evidence.gap_areas[:2]:
            questions.append(f"你怎么看待{gap}？有相关学习计划吗？")

        plan = [
            "Day 1-2: 复习核心技术栈",
            "Day 3-4: 准备项目介绍 + 刷题",
            "Day 5-6: 模拟面试练习",
            "Day 7: 轻复习 + 准备反问",
        ]

        return InterviewPrep(
            likely_questions=questions,
            prep_plan_7day=plan,
            focus_areas=evidence.gap_areas[:4] + skills[:2],
        )

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
