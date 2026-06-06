"""
Resume Evidence Agent — 从简历中提取真实证据，不编造。

核心能力：
- 找出简历中真实存在的技能证据（引用原文片段）
- 找出项目证据
- 找出量化指标
- 找出 LLM/Agent 相关经验
- 标记明显缺失的方向
"""

import json
from agent_state import ResumeEvidence

_PROMPT = """你是一位严格的技术面试官。请仔细阅读候选人简历，找出每个能力点的证据。

重要约束：只能引用简历中真实存在的内容作为证据，绝不编造。

输出 JSON：
{
  "skill_evidence": {
    "Python": ["简历片段：用Python开发了推荐系统"],
    "PyTorch": ["简历片段：基于PyTorch实现了Transformer模型"]
  },
  "project_evidence": {
    "GenAdRec": ["简历片段：Transformer-based用户行为序列建模"]
  },
  "metrics_evidence": ["简历片段：NDCG@10提升3.2%"],
  "llm_evidence": ["简历片段：使用DeepSeek API实现JD检索"],
  "agent_evidence": ["简历片段：Multi-Agent协作系统"],
  "gap_areas": ["缺少LangGraph项目经验", "缺少Agent评测经验"]
}

规则：
- skill_evidence：每个技能必须有对应的简历原文片段作为证据
- project_evidence：每个项目名称对应其证据片段
- metrics_evidence：简历中的所有量化指标
- llm_evidence：与LLM/RAG/Agent相关的经验证据
- agent_evidence：具体Agent相关经验
- gap_areas：根据求职方向，列出简历明显缺失但重要的能力

简历文本：
{resume}

求职方向（来自 CareerIntent）：{direction}"""


class ResumeEvidenceAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def run(self, resume: str, direction: str = "") -> ResumeEvidence:
        if self.llm and self.llm.available:
            prompt = _PROMPT.replace("{resume}", resume[:3000]).replace("{direction}", direction or "AI算法")
            try:
                resp = self.llm.chat(prompt, temperature=0.2, max_tokens=1200)
                data = self._parse_json(resp)
                return ResumeEvidence(
                    skill_evidence=data.get("skill_evidence", {}),
                    project_evidence=data.get("project_evidence", {}),
                    metrics_evidence=data.get("metrics_evidence", []),
                    llm_evidence=data.get("llm_evidence", []),
                    agent_evidence=data.get("agent_evidence", []),
                    gap_areas=data.get("gap_areas", []),
                )
            except Exception:
                pass
        return self._fallback(resume, direction)

    def _fallback(self, resume: str, direction: str) -> ResumeEvidence:
        """规则版证据提取"""
        r = resume.lower()
        skills_map = {
            "python": ["python" in r],
            "pytorch": ["pytorch" in r],
            "transformer": ["transformer" in r],
            "rag": ["rag" in r],
            "agent": ["agent" in r],
            "faiss": ["faiss" in r],
            "langchain": ["langchain" in r],
            "c++": ["c++" in r or "cpp" in r],
            "sql": ["sql" in r],
            "docker": ["docker" in r],
        }
        evidence = {k: [f"规则检测：简历包含{k}"] for k, v in skills_map.items() if v[0]}

        return ResumeEvidence(
            skill_evidence=evidence,
            llm_evidence=["LLM相关经验" if any(k in r for k in ["llm", "rag", "agent", "deepseek"]) else ""],
            agent_evidence=["Agent经验" if "agent" in r or "langgraph" in r else ""],
            gap_areas=["缺少Agent框架项目" if "langgraph" not in r and "agent" in direction.lower() else ""],
        )

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
