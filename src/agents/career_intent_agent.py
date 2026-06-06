"""
Career Intent Agent — 从简历+目标中推断求职方向、阶段、偏好。

核心能力：
- 判断用户真实求职方向（大模型算法/LLM应用算法/Agent算法等）
- 判断阶段（实习/校招/提前批）
- 推断城市偏好、薪资偏好、风险偏好
- 输出结构化 JSON
"""

import json
from typing import Optional
from agent_state import CareerIntent

_PROMPT = """你是一位资深技术猎头，专门为 AI 方向候选人判断求职定位。

请根据候选人简历和目标，输出 JSON（不要 markdown codeblock，直接 JSON）：

{{
  "direction": "大模型算法 | LLM应用算法 | Agent算法 | 推荐算法 | 推荐转大模型 | 后端转AI | 数据分析 | 其他",
  "stage": "实习 | 校招 | 提前批",
  "target_cities": ["深圳", "北京"],
  "salary_min": null,
  "risk_preference": "稳妥 | 平衡 | 冲刺",
  "reasoning": "判断理由（2-3句）"
}}

判断规则：
1. 方向：看简历技能和项目关键词。Transformer/PyTorch/大模型训练 → 大模型算法；LangChain/LlamaIndex/RAG/Agent搭建 → LLM应用算法；两者都有 → 看项目侧重点
2. 阶段：2026届 → 校招；2027届及以后 → 实习；有"提前批"字样 → 提前批
3. 城市：从简历或目标中提取，默认["深圳", "北京"]
4. risk_preference：简历项目丰富 → 冲刺；项目中等 → 平衡；项目较少 → 稳妥

简历文本：
{resume}

用户目标（可为空）：
{goal}"""

_FALLBACK_PROMPT = """简历太短或信息不足，请基于以下有限信息尽力判断：

简历片段：{resume}
目标：{goal}

输出 JSON 格式。如果某字段无法判断，direction 填 "待确认"，stage 填 "校招"。"""


class CareerIntentAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def run(self, resume: str, goal: str = "") -> CareerIntent:
        trace = "[CareerIntent] "

        if self.llm and self.llm.available:
            prompt = _PROMPT.format(resume=resume[:3000], goal=goal or "未指定")
            try:
                resp = self.llm.chat(prompt, temperature=0.3, max_tokens=600)
                data = self._parse_json(resp)
                trace += f"LLM判断方向={data.get('direction', '?')}"
                return CareerIntent(
                    direction=data.get("direction", "待确认"),
                    stage=data.get("stage", "校招"),
                    target_cities=data.get("target_cities", ["深圳"]),
                    salary_min=data.get("salary_min"),
                    risk_preference=data.get("risk_preference", "平衡"),
                    reasoning=data.get("reasoning", ""),
                )
            except Exception as e:
                trace += f"LLM失败: {e}"

        # Fallback: 规则推断
        trace += "fallback规则推断"
        return self._fallback(resume, goal, trace)

    def _fallback(self, resume: str, goal: str, trace: str = "") -> CareerIntent:
        r = resume.lower()

        # 方向判断
        direction = "待确认"
        if any(k in r for k in ["langgraph", "agent", "multi agent", "多 agent", "智能体"]):
            direction = "Agent算法"
        elif any(k in r for k in ["rag", "langchain", "llamaindex", "embedding", "faiss"]):
            direction = "LLM应用算法"
        elif any(k in r for k in ["transformer", "pytorch", "finetune", "微调", "sft", "dpo", "rlhf"]):
            direction = "大模型算法"
        elif "推荐" in r or "recommend" in r:
            direction = "推荐转大模型"

        # 阶段判断
        stage = "校招"
        if "2027" in resume or "研一" in r or "大二" in r or "大三" in r:
            stage = "实习"
        if "提前批" in r or "提前批" in goal:
            stage = "提前批"

        # 城市
        cities = ["深圳", "北京"]
        if "上海" in resume + goal:
            cities.insert(0, "上海")
        if "杭州" in resume + goal:
            cities.insert(0, "杭州")

        # 风险偏好
        risk = "平衡"
        signals = r.count("项目") + r.count("project")
        if signals >= 4:
            risk = "冲刺"
        elif signals <= 1:
            risk = "稳妥"

        return CareerIntent(
            direction=direction,
            stage=stage,
            target_cities=cities,
            risk_preference=risk,
            reasoning=f"规则推断: 方向={direction}, 阶段={stage}",
        )

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
