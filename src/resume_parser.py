import re


SKILL_CATALOG = [
    # LLM / NLP
    "LLM", "RAG", "Agent", "Embedding", "Faiss", "LangChain", "Prompt",
    "BERT", "GPT", "T5", "Llama", "Qwen", "ChatGLM", "DeepSeek",
    "文本分类", "命名实体识别", "NER", "Seq2Seq", "Attention", "Beam Search",
    "自然语言处理", "NLP", "文本生成", "摘要生成", "信息抽取",
    # 推荐 / 搜索
    "推荐系统", "召回", "排序", "重排", "NDCG", "A/B Test", "CTR",
    "搜索", "Query 理解", "意图识别", "向量检索", "多兴趣", "Semantic ID",
    "Wide&Deep", "DeepFM", "DIN", "DIEN", "MIND",
    # CV
    "TensorFlow", "PyTorch", "OpenCV", "YOLO", "图像分类", "目标检测",
    "计算机视觉", "CV", "分割", "Transformer", "ViT",
    # 后端 / 基础
    "Python", "Java", "Go", "Golang", "C++", "Rust",
    "Docker", "Kubernetes", "K8s", "微服务", "gRPC", "Thrift", "RPC",
    "MySQL", "Redis", "Kafka", "消息队列", "Consul", "etcd",
    "FastAPI", "Flask", "Spring", "Django", "Gin",
    # 数据 / 分析
    "SQL", "Hadoop", "Spark", "Flink", "Hive", "Pandas", "NumPy", "Matplotlib",
    "数据分析", "数据可视化", "指标体系", "漏斗分析", "AUC", "ROC",
    # ML / DL 基础
    "机器学习", "深度学习", "强化学习", "scikit-learn", "XGBoost", "LightGBM",
    "模型训练", "模型评估", "特征工程",
    # LLM 工程
    "多轮对话", "Function Calling", "Tool Use", "思维链", "CoT",
    "混合检索", "Hybrid Search", "Reranker", "重排序",
    "Prompt Engineering", "Few-shot", "RLHF", "SFT",
    # 其他
    "产品设计", "可视化", "多模态", "CLIP", "Stable Diffusion",
]


PROJECT_SIGNAL_CATALOG = [
    "Semantic ID", "rerank", "MIND", "简历", "JD", "岗位",
    "检索", "评估", "Demo", "用户兴趣", "多兴趣", "生成式推荐",
]


def contains(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def parse_resume(resume_text: str) -> dict:
    """Rule-based parser used as the stable fallback for Resume Parser Agent."""
    resume_text = resume_text or ""
    skills = [skill for skill in SKILL_CATALOG if contains(resume_text, skill)]
    project_signals = [
        signal for signal in PROJECT_SIGNAL_CATALOG if contains(resume_text, signal)
    ]
    project_signals = list(dict.fromkeys(project_signals + skills))

    has_metrics = bool(
        re.search(r"ndcg|hitrate|auc|准确率|召回率|提升|%|topk", resume_text, re.I)
    )
    has_llm_project = bool(
        re.search(r"llm|rag|agent|prompt|deepseek|openai|通义|混元", resume_text, re.I)
    )
    has_rec_project = bool(
        re.search(r"推荐|召回|排序|mind|semantic id|rerank|用户兴趣", resume_text, re.I)
    )

    return {
        "skills": skills,
        "project_signals": project_signals,
        "has_metrics": has_metrics,
        "has_llm_project": has_llm_project,
        "has_rec_project": has_rec_project,
        "raw_text": resume_text,
    }


# ---------------------------------------------------------------------------
# LLM 增强解析（可选，失败自动 fallback 到规则版 parse_resume）
# ---------------------------------------------------------------------------

RESUME_LLM_SCHEMA = """{
  "skills": ["技能列表"],
  "project_signals": ["项目信号词"],
  "has_metrics": true/false,
  "has_llm_project": true/false,
  "has_rec_project": true/false
}"""

RESUME_LLM_PROMPT = """你是一个简历解析器。请从以下简历文本中提取结构化信息，严格按 JSON Schema 输出。

Schema:
{schema}

要求：
1. 只输出 JSON，不要输出任何其他文字
2. skills 提取所有明确提到的技术名称
3. has_metrics 判断是否有量化指标（NDCG、准确率、提升 x%、TopK 等）
4. has_llm_project 判断是否有 LLM/RAG/Agent/Prompt 相关项目
5. has_rec_project 判断是否有推荐/召回/排序相关项目
6. project_signals 提取项目相关关键词

简历文本：
{resume_text}"""


def parse_resume_with_llm(resume_text: str, llm_client=None) -> dict:
    """LLM 增强简历解析，失败自动 fallback 到 parse_resume。"""
    if llm_client is None:
        return parse_resume(resume_text)
    try:
        from src.llm_client import LLMClient
        if not isinstance(llm_client, LLMClient) or not llm_client.available:
            return parse_resume(resume_text)
    except ImportError:
        return parse_resume(resume_text)

    prompt = RESUME_LLM_PROMPT.format(schema=RESUME_LLM_SCHEMA, resume_text=resume_text[:3000])
    result = llm_client.chat_json("你是精确的简历解析器。", prompt)
    if result is None:
        return parse_resume(resume_text)

    # 校验 + 补全
    for key in ["skills", "project_signals"]:
        if key not in result or not isinstance(result.get(key), list):
            result[key] = []
    for key in ["has_metrics", "has_llm_project", "has_rec_project"]:
        if key not in result:
            result[key] = False
    result["raw_text"] = resume_text
    return result
