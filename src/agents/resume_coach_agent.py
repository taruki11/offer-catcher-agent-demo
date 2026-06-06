"""
Resume Coach Agent — 基于真实证据改写简历。

严格规则：
- 只改写简历中真实存在的经历
- 如果简历没有证据，标记为"需要先补经历"
- 不编造、不夸张
"""

import json
from agent_state import CoachOutput, ResumeEvidence, JDProfile

_PROMPT = """你是简历优化教练。基于候选人真实简历证据和目标 JD，给出简历改写建议。

关键约束：绝不能编造经历。只能基于候选人真实存在的经验进行表达优化。

输出 JSON：
{
  "can_rewrite": [
    "将'做了个Agent项目'改写为'基于LangGraph实现多Agent协作系统，自动完成XX任务，效率提升40%'"
  ],
  "need_project_first": [
    "LangGraph经验：简历中未找到相关项目，建议先动手做一个多Agent Demo再写入简历"
  ],
  "dont_fabricate": [
    "不要写'精通大模型训练'：简历中只有推理经验，没有训练经验"
  ],
  "optimized_resume_fragments": {
    "项目1": "优化后的项目描述",
    "技能部分": "优化表达后的技能列表"
  }
"""


class ResumeCoachAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def coach(self, resume: str, evidence: ResumeEvidence, target_jd: JDProfile | None = None) -> CoachOutput:
        if self.llm and self.llm.available:
            jd_info = f"目标岗位: {target_jd.title}@{target_jd.company}, skills={target_jd.hard_skills}" if target_jd else "无特定目标岗位"
            prompt = f"{_PROMPT}\n\n简历：\n{resume[:2000]}\n\n真实证据：\n{json.dumps({'skills': list(evidence.skill_evidence.keys()), 'gaps': evidence.gap_areas}, ensure_ascii=False)}\n\n{jd_info}"
            try:
                resp = self.llm.chat(prompt, temperature=0.3, max_tokens=1000)
                data = self._parse_json(resp)
                return CoachOutput(
                    can_rewrite=data.get("can_rewrite", []),
                    need_project_first=data.get("need_project_first", []),
                    dont_fabricate=data.get("dont_fabricate", []),
                    optimized_resume_fragments=data.get("optimized_resume_fragments", {}),
                )
            except Exception:
                pass
        return self._fallback(resume, evidence)

    def _fallback(self, resume: str, evidence: ResumeEvidence) -> CoachOutput:
        can = []
        need = []
        dont = []

        # 可优化的点
        if evidence.skill_evidence:
            skills = ", ".join(list(evidence.skill_evidence.keys())[:6])
            can.append(f"技能总结：用一段话串联核心技能：{skills}")

        # 缺口
        for gap in evidence.gap_areas[:3]:
            need.append(f"需要先补充：{gap}")

        dont.append("不要夸张项目经历，保持真实性")
        return CoachOutput(can_rewrite=can, need_project_first=need, dont_fabricate=dont)

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
