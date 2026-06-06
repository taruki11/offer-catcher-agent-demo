"""
JD Analyst Agent — 阅读岗位 JD，抽取结构化岗位画像。

核心能力：
- 从 JD 文本中抽取硬技能、软技能、业务方向
- 识别学历要求、加分项、隐含门槛
- 输出标准 JD schema
"""

import json
from agent_state import JDProfile

_PROMPT = """你是招聘 JD 分析师。阅读以下岗位描述，输出结构化 JSON：

{
  "hard_skills": ["Python", "PyTorch", "Transformer"],
  "soft_skills": ["沟通能力", "团队协作"],
  "education": "本科及以上 | 硕士及以上 | 博士",
  "bonus_points": ["有顶会论文加分", "有开源项目加分"],
  "hidden_requirements": ["实际要求3年以上经验", "隐含要求211以上学历"],
  "direction": "大模型算法 | LLM应用算法 | Agent算法 | 推荐算法 | 后端 | 其他",
  "stage": "实习 | 校招 | 社招"
}

规则：
- hard_skills：技术栈关键词（编程语言、框架、工具）
- soft_skills：软性要求
- hidden_requirements：JD 没说但实际可能卡的条件
- direction：从这个 JD 看属于哪个算法方向
- 如果某字段没有信息，用空列表或空字符串

JD 文本：
{jd_text}"""


class JDAnalystAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def analyze(self, jd_text: str, fallback_data: dict | None = None) -> JDProfile:
        """分析单个 JD，返回 JDProfile。fallback_data 来自 JobScout 的预填充。"""
        fb = fallback_data or {}

        if self.llm and self.llm.available and len(jd_text) > 30:
            prompt = _PROMPT.replace("{jd_text}", jd_text[:2500])
            try:
                resp = self.llm.chat(prompt, temperature=0.2, max_tokens=800)
                data = self._parse_json(resp)
                return JDProfile(
                    title=fb.get("title", ""),
                    company=fb.get("company", ""),
                    city=fb.get("city", ""),
                    salary=fb.get("salary", ""),
                    source_url=fb.get("source_url", fb.get("url", "")),
                    jd_text=jd_text,
                    hard_skills=data.get("hard_skills", []),
                    soft_skills=data.get("soft_skills", []),
                    education=data.get("education", ""),
                    bonus_points=data.get("bonus_points", []),
                    hidden_requirements=data.get("hidden_requirements", []),
                    direction=data.get("direction", ""),
                    stage=data.get("stage", ""),
                )
            except Exception:
                pass

        # Fallback: keyword extraction
        return self._fallback(jd_text, fb)

    def _fallback(self, jd_text: str, fb: dict) -> JDProfile:
        skills = []
        keywords = ["python", "pytorch", "tensorflow", "transformer", "rag", "agent",
                     "langchain", "faiss", "embedding", "c++", "cuda", "triton",
                     "deepspeed", "vllm", "docker", "kubernetes", "sql"]
        for kw in keywords:
            if kw in jd_text.lower():
                skills.append(kw.title() if len(kw) > 3 else kw.upper())

        return JDProfile(
            title=fb.get("title", ""),
            company=fb.get("company", ""),
            city=fb.get("city", ""),
            salary=fb.get("salary", ""),
            source_url=fb.get("source_url", fb.get("url", "")),
            jd_text=jd_text,
            hard_skills=skills,
        )

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
