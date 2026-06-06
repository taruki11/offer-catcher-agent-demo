"""
jd_parser.py — JD 文本解析器（规则版）
将自由文本 JD 转为标准化 dict，与 jobs.json 结构兼容。
"""
from __future__ import annotations

import re
from typing import Optional

# 方向映射（JD 关键词 → direction 标签）
DIRECTION_KEYWORDS = {
    "大模型应用": "大模型应用算法", "LLM": "大模型应用算法", "Agent": "大模型应用算法",
    "RAG": "大模型应用算法", "大模型算法": "大模型应用算法",
    "推荐算法": "推荐算法", "推荐系统": "推荐算法", "推荐排序": "推荐算法",
    "搜索算法": "大模型应用算法", "检索": "大模型应用算法",
    "自然语言处理": "大模型应用算法", "NLP": "大模型应用算法",
    "计算机视觉": "大模型应用算法", "CV": "大模型应用算法", "YOLO": "大模型应用算法",
    "后端研发": "后端研发", "后端开发": "后端研发", "Go": "后端研发",
    "数据分析": "数据分析", "SQL": "数据分析",
    "产品经理": "产品经理",
    "匹配算法": "大模型应用算法", "人岗匹配": "大模型应用算法",
}

SKILL_PATTERNS = [
    "Python", "PyTorch", "TensorFlow", "Transformer", "BERT", "GPT", "LLM",
    "RAG", "Agent", "Embedding", "LangChain", "FAISS", "Faiss",
    "推荐系统", "召回", "排序", "NDCG", "A/B Test", "ABTest", "A/B 测试",
    "Prompt", "Prompt Engineering", "Prompt 工程",
    "语义检索", "向量检索", "搜索", "重排", "rerank",
    "Java", "Go", "C\\+\\+", "Rust", "Scala",
    "Docker", "Kubernetes", "K8s", "gRPC", "微服务",
    "MySQL", "Redis", "Kafka", "MongoDB", "Elasticsearch",
    "SQL", "Spark", "Hadoop", "数据仓库",
    "模型微调", "LoRA", "QLoRA", "SFT", "RLHF",
    "OpenCV", "YOLO", "目标检测", "图像分类",
    "自然语言处理", "NLP", "命名实体识别", "NER", "文本分类", "Seq2Seq", "摘要生成",
    "Beam Search", "Attention",
    "数据清洗", "特征工程", "模型部署",
]


def parse_jd(jd_text: str) -> dict:
    """解析单个 JD 文本，返回标准化 dict。"""
    text = jd_text.strip()
    lines = text.split("\n")

    title = _extract_title(lines, text)
    company = _extract_company(lines, text)
    city = _extract_city(lines, text)
    stage = _extract_stage(lines, text)
    direction = _infer_direction(title, text)
    skills = _extract_skills(text)
    project_signals = _extract_project_signals(text, skills)
    hard_requirements = _extract_hard_requirements(text)
    bonus_requirements = _extract_bonus_requirements(text)
    risk_flags = _extract_risk_flags(text)
    interview_themes = _infer_interview_themes(skills, text)

    return {
        "id": f"user_{_hash_title(title)}",
        "title": title,
        "company": company,
        "city": city,
        "direction": direction,
        "stage": stage,
        "skills": skills,
        "project_signals": project_signals,
        "jd": text[:500],
        "hard_requirements": hard_requirements,
        "bonus_requirements": bonus_requirements,
        "risk_flags": risk_flags,
        "interview_themes": interview_themes,
        "source": "user_pasted",
        "raw_text": text,
    }


def _hash_title(title: str) -> str:
    h = 0
    for c in title:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return hex(h)[2:]


def _extract_title(lines: list[str], text: str) -> str:
    # 优先从第一行提取
    first = lines[0].strip().lstrip("#").strip()
    # 去掉常见前缀
    for prefix in ["岗位：", "职位：", "岗位名称：", "标题：", "Title:"]:
        if first.startswith(prefix):
            first = first[len(prefix):].strip()
    if first and len(first) < 50:
        if any(kw in first for kw in ["算法", "实习", "工程师", "开发", "产品", "数据"]):
            return first
    for line in lines:
        s = line.strip().lstrip("#").strip()
        for prefix in ["岗位：", "职位："]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
        if any(kw in s for kw in ["实习生", "工程师", "岗位"]) and len(s) < 60:
            return s
    return "算法岗位"


def _extract_company(lines: list[str], text: str) -> str:
    pat = re.compile(r"(公司|部门|事业群|企业)[：:]\s*(.+)")
    m = pat.search(text)
    if m:
        return m.group(2).strip()[:30]
    for kw in ["腾讯", "字节", "阿里", "百度", "美团", "快手", "小红书", "B站", "微软", "Google"]:
        if kw in text:
            return kw
    return "未知公司"


def _extract_city(lines: list[str], text: str) -> str:
    cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京", "苏州", "西安"]
    for c in cities:
        if c in text:
            return c
    pat = re.compile(r"(城市|地点|工作地点)[：:]\s*(.+)")
    m = pat.search(text)
    if m:
        return m.group(2).strip()[:20]
    return "不限"


def _extract_stage(lines: list[str], text: str) -> str:
    if "实习" in text:
        return "实习"
    if "校招" in text or "应届" in text or "毕业" in text:
        return "校招"
    if "社招" in text or "经验" in text or "年以" in text:
        return "社招"
    return "不限"


def _infer_direction(title: str, text: str) -> str:
    combined = title + " " + text
    # 按优先级匹配
    for kw, direction in DIRECTION_KEYWORDS.items():
        if kw.lower() in combined.lower():
            return direction
    # 从 title 推断
    if "算法" in title:
        return "大模型应用算法"
    if "后端" in title or "研发" in title:
        return "后端研发"
    return "通用"


def _extract_skills(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for skill in SKILL_PATTERNS:
        if skill.lower() in text_lower:
            found.append(skill)
    # 去重 + 保持顺序
    seen = set()
    result = []
    for s in found:
        if s.lower() not in seen:
            result.append(s)
            seen.add(s.lower())
    return result[:20]


def _extract_project_signals(text: str, skills: list[str]) -> list[str]:
    signals = []
    # 从 skills 中选最具项目信号价值的
    signal_keywords = {
        "RAG", "Agent", "Embedding", "Transformer", "微服务", "推荐系统",
        "召回", "排序", "重排", "检测", "识别", "分类", "搜索",
        "LLM", "Prompt", "模型部署", "模型微调", "LoRA",
    }
    for s in skills:
        if s in signal_keywords:
            signals.append(s)
    return signals[:10]


def _extract_hard_requirements(text: str) -> list[str]:
    reqs = []
    if "Python" in text: reqs.append("熟练使用 Python")
    if "PyTorch" in text or "TensorFlow" in text: reqs.append("熟悉 PyTorch / TensorFlow")
    if "硕士" in text or "研究生" in text: reqs.append("硕士及以上学历")
    if "本科" in text: reqs.append("本科及以上学历")
    if any(kw in text for kw in ["3 年", "3年", "三年", "5 年", "5年"]): reqs.append("相关经验")
    return reqs or ["具备基本编程能力"]


def _extract_bonus_requirements(text: str) -> list[str]:
    bonus = []
    for kw in ["LLM", "大模型", "Agent", "RAG", "论文", "开源", "Kaggle"]:
        if kw in text:
            bonus.append(f"有 {kw} 经验者优先")
    return bonus[:5]


def _extract_risk_flags(text: str) -> list[str]:
    flags = []
    if "5 年" in text or "5年" in text or "资深" in text:
        flags.append("要求较高经验")
    if "985" in text or "211" in text or "一本" in text:
        flags.append("学历门槛")
    return flags


def _infer_interview_themes(skills: list[str], text: str) -> list[str]:
    themes = []
    skill_set = {s.lower() for s in skills}
    if "rag" in skill_set or "检索" in skill_set: themes.append("RAG 检索增强")
    if "agent" in skill_set: themes.append("Agent 工具调用")
    if "transformer" in skill_set: themes.append("Transformer 原理")
    if "推荐系统" in skill_set or "召回" in skill_set: themes.append("推荐系统与召回排序")
    if "embedding" in skill_set: themes.append("Embedding 与向量检索")
    if "模型微调" in skill_set or "lora" in skill_set: themes.append("模型微调技术")
    if not themes: themes = ["算法基础", "项目深挖", "系统设计"]
    return themes[:4]


# ---------------------------------------------------------------------------
# LLM 增强解析（可选，失败自动 fallback 到规则版）
# ---------------------------------------------------------------------------

JD_LLM_SCHEMA = """{
  "title": "岗位名称",
  "company": "公司/部门",
  "city": "城市",
  "direction": "技术方向（大模型应用算法/推荐算法/后端研发/数据分析/产品经理）",
  "stage": "阶段（实习/校招/社招）",
  "skills": ["要求的技能列表"],
  "project_signals": ["项目信号词"],
  "hard_requirements": ["硬性要求"],
  "bonus_requirements": ["加分项"],
  "risk_flags": ["潜在风险提示"],
  "interview_themes": ["面试主题"]
}"""

JD_LLM_PROMPT = """你是一个岗位 JD 解析器。请从以下 JD 文本中提取结构化信息，严格按 JSON Schema 输出。

Schema:
{schema}

要求：
1. 只输出 JSON，不要输出任何其他文字
2. skills 只提取 JD 中明确提到或强烈暗示的技术名称
3. direction 从 大模型应用算法/推荐算法/后端研发/数据分析/产品经理 中选择最匹配的
4. stage 从 实习/校招/社招 中选择
5. 如果某字段无法确定，填写空列表或"不限"

JD 文本：
{jd_text}"""


def parse_jd_with_llm(jd_text: str, llm_client=None) -> dict:
    """LLM 增强 JD 解析，失败自动 fallback 到 parse_jd。"""
    if llm_client is None:
        return parse_jd(jd_text)
    try:
        from src.llm_client import LLMClient
        if not isinstance(llm_client, LLMClient) or not llm_client.available:
            return parse_jd(jd_text)
    except ImportError:
        return parse_jd(jd_text)

    prompt = JD_LLM_PROMPT.format(schema=JD_LLM_SCHEMA, jd_text=jd_text[:3000])
    result = llm_client.chat_json("你是精确的岗位 JD 解析器。", prompt)
    if result is None:
        return parse_jd(jd_text)  # LLM 失败 → fallback

    # 校验 + 补全。LLM 输出只作为结构化候选，类型不可信时退回规则值。
    fallback = parse_jd(jd_text)
    scalar_keys = ["title", "company", "city", "direction", "stage"]
    list_keys = [
        "skills",
        "project_signals",
        "hard_requirements",
        "bonus_requirements",
        "risk_flags",
        "interview_themes",
    ]
    for key in scalar_keys:
        if not isinstance(result.get(key), str) or not result.get(key, "").strip():
            result[key] = fallback.get(key, "不限")
    for key in list_keys:
        if not isinstance(result.get(key), list):
            result[key] = fallback.get(key, [])
        else:
            result[key] = [str(item).strip() for item in result[key] if str(item).strip()]
    if not result["skills"]:
        result["skills"] = fallback.get("skills", [])
    if not result["project_signals"]:
        result["project_signals"] = fallback.get("project_signals", [])
    if not result["interview_themes"]:
        result["interview_themes"] = fallback.get("interview_themes", ["项目深挖"])
    result["id"] = f"llm_{_hash_title(result.get('title', ''))}"
    result["jd"] = jd_text[:500]
    result["source"] = "user_pasted"
    result["raw_text"] = jd_text
    return result
