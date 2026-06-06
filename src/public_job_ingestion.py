"""
public_job_ingestion.py — 公开岗位数据接入与标准化模块

功能：
1. 从外部原始数据（dict）标准化为项目统一 job schema
2. 推断方向、阶段、技能、面试主题
3. 数据质量评分和去重
4. 合并内置岗位与公开岗位

不依赖外部网络，可离线运行。
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

# ---------------------------------------------------------------------------
# 方向映射
# ---------------------------------------------------------------------------

DIRECTION_KEYWORDS = {
    "LLM": ["大模型", "llm", "large language model", "language model", "chatgpt", "gpt", "deepseek", "glm",
            "generative ai", "generativeai", "gen ai", "genai"],
    "Agent": ["agent", "智能体", "智能助手", "multi-agent", "multi agent", "autonomous agent"],
    "NLP": ["nlp", "natural language", "自然语言", "文本", "语义", "翻译", "bert", "命名实体", "情感分析",
            "自然言语", "seq2seq", "text classification", "text generation", "named entity"],
    "推荐算法": ["推荐", "recommend", "recsys", "cf", "collaborative filter", "排序", "rank",
                  "wide&deep", "ctr", "cvr", "ndcg", "召回", "recall"],
    "深度学习": ["deep learning", "深度学习", "neural network", "神经网络", "cnn", "rnn", "lstm",
                  "transformer", "attention", "预训练", "pretrain", "machine learning", "ml engineer"],
    "计算机视觉": ["cv", "computer vision", "视觉", "图像", "目标检测", "object detection", "分割",
                   "segmentation", "yolo", "resnet", "vgg", "gan", "diffusion", "检测", "识别",
                   "image recognition", "image classification"],
    "后端开发": ["后端", "backend", "back-end", "server", "golang", "go", "java", "微服务",
                  "microservice", "api", "k8s", "docker", "grpc", "消息队列", "mysql", "redis",
                  "messaging", "message queue"],
    "数据分析": ["数据分析", "data analy", "data scien", "sql", "bi", "excel", "tableau",
                  "指标体系", "数据可视化", "data visual", "ab测试", "a/b test", "用户画像", "analytics"],
    "搜索算法": ["搜索", "search", "query", "query理解", "信息检索", "information retrieval",
                  "es", "elasticsearch", "ranking", "索引", "indexing"],
    "前端开发": ["前端", "frontend", "front-end", "react", "vue", "angular", "javascript",
                  "typescript", "html", "css", "web developer"],
    "ML平台/Infra": ["platform", "infra", "ml platform", "ai platform", "训练框架", "推理",
                      "model serving", "triton", "tensorrt", "mlops", "ml ops", "ml infrastructure",
                      "ai infrastructure"],
    "自动驾驶": ["自动驾驶", "autonomous", "self-driving", "perception", "规划", "control",
                  "lidar", "ros", "slam", "robotics", "机器人"],
    "语音算法": ["语音", "speech", "asr", "tts", "声学", "降噪", "audio"],
    "安全算法": ["安全", "security", "cyber", "攻防", "漏洞", "anti-fraud", "反欺诈",
                 "cryptograph", "penetration", "vulnerability"],
}

STAGE_KEYWORDS = {
    "实习": ["intern", "internship", "实习生", "intern"],
    "校招": ["校招", "campus", "graduate", "应届", "new grad",
             "junior", "entry level", "初級", "entry-level"],
    "社招": ["senior", "staff", "principal", "lead", "manager",
             "高级", "资深", "专家", "负责人", "lead"],
    "不限": [],
}

SKILL_PATTERN = re.compile(
    r"\b(python|pytorch|tensorflow|java|go(lang)?|c\+\+|rust|scala|sql|spark|hadoop|flink|"
    r"kafka|redis|mysql|postgres|mongodb|elasticsearch|docker|kubernetes|k8s|git|linux|"
    r"aws|gcp|azure|transformers|huggingface|langchain|llamaindex|bert|gpt|llama|deepseek|"
    r"glm|llm|rag|agent|embedding|faiss|chroma|milvus|pinecone|weaviate|"
    r"推荐系统|协同过滤|矩阵分解|wide&deep|deepfm|ndcg|ab.test|ctr|cvr|"
    r"ner|文本分类|textcnn|lstm|seq2seq|attention|"
    r"yolo|resnet|vgg|gan|diffusion|stable.diffusion|openpose|"
    r"react|vue|angular|javascript|typescript|html|css|node\.js|"
    r"grpc|protobuf|微服务|django|fastapi|flask|spring)\b",
    re.IGNORECASE,
)

PROJECT_SIGNALS = {
    "RAG": ["rag", "检索增强", "retrieval.augmented", "知识库"],
    "Agent": ["agent", "智能体", "工具调用", "function.calling", "multi.agent"],
    "FineTune": ["微调", "finetune", "lora", "qlora", "sft", "dpo"],
    "Embedding": ["embedding", "向量", "vector", "faiss", "chroma"],
    "Recommendation": ["推荐", "recommend", "recsys", "ndcg", "hitrate",
                       "recall", "ctr", "排序"],
    "NLP_Classic": ["ner", "文本分类", "textcnn", "seq2seq", "bert"],
    "CV_Traditional": ["yolo", "目标检测", "resnet", "分类"],
    "Backend": ["grpc", "微服务", "k8s", "消息队列", "分布式", "高并发"],
    "DataAnalysis": ["数据分析", "指标", "可视化", "ab.test", "sql"],
    "Deployment": ["部署", "deploy", "docker", "tensorrt", "triton"],
}

INTERVIEW_THEMES_BY_DIRECTION = {
    "LLM": ["RAG召回策略与优化", "Agent工作流设计与兜底", "Prompt工程最佳实践",
            "大模型微调(LoRA/QLoRA)", "向量数据库选型(Faiss/Chroma/Milvus)"],
    "推荐算法": ["召回-粗排-精排 pipeline", "多目标优化(MMoE/PLE)",
                 "冷启动与探索策略", "特征工程与实时特征", "A/B实验设计与评估"],
    "NLP": ["Transformer架构与变体", "预训练语言模型(BERT/GPT)",
            "Seq2Seq与Attention机制", "NER/文本分类/摘要模型", "Prompt Tuning vs FineTuning"],
    "计算机视觉": ["Backbone网络演进(ResNet/ViT)", "目标检测(YOLO/DETR)",
                  "图像分割(U-Net/MaskRCNN)", "生成模型(GAN/Diffusion)", "模型轻量化与部署"],
    "后端开发": ["Go并发模型与GC优化", "分布式一致性(Raft/Paxos)",
                 "消息队列(Kafka/RabbitMQ)", "微服务治理(服务发现/熔断/限流)", "MySQL索引与慢查询优化"],
    "数据分析": ["指标体系设计与北极星指标", "漏斗分析与用户画像",
                 "A/B实验统计方法", "SQL高级查询与优化", "数据可视化(Python/Tableau)"],
    "搜索算法": ["Query理解(纠错/改写/意图)", "倒排索引与向量检索融合",
                 "排序模型(LTR/LambdaMART)", "相关性评估(NDCG/MRR)", "Query-文档匹配"],
    "ML平台": ["模型服务(Triton/TF Serving)", "特征平台与样本拼接",
               "训练框架(PyTorch DDP/DeepSpeed)", "MLflow与实验管理", "GPU集群调度"],
}


# ---------------------------------------------------------------------------
# 标准化函数
# ---------------------------------------------------------------------------

def normalize_public_job(raw: dict) -> dict | None:
    """
    将原始公开岗位 dict 标准化为项目统一 schema。
    返回 None 表示数据不合格，应该丢弃。
    """
    title = _safe_str(raw.get("title", "") or raw.get("job_title", ""))
    if not title:
        return None

    company = _safe_str(raw.get("company", "") or raw.get("company_name", "")
                        or raw.get("organization", "") or "未知公司")
    description = _safe_str(
        raw.get("description", "")
        or raw.get("description_html", "")
        or raw.get("description_md", "")
        or raw.get("body", "")
        or ""
    )

    # 过短描述过滤
    if len(description.strip()) < 50:
        description = title  # 用标题当最简描述

    # 位置
    raw_location = _safe_str(raw.get("location", "") or raw.get("locations", "")
                             or raw.get("city", ""))
    city = _infer_city(raw_location)

    # seniority / stage
    seniority = _safe_str(raw.get("seniority", "") or raw.get("employment_type", "")
                          or raw.get("level", "") or "")
    stage = infer_stage(title, seniority, raw.get("employment_type", ""))

    # 方向
    direction = infer_direction(title, description, [])

    # 技能提取
    raw_skills = _find_skills(description)
    if raw.get("skills"):
        extra = [_safe_str(s) for s in raw["skills"]] if isinstance(raw["skills"], list) else []
        for s in extra:
            if s and s not in raw_skills:
                raw_skills.append(s)
    if raw.get("tech_stack") or raw.get("stack"):
        stack = raw.get("tech_stack") or raw.get("stack")
        if isinstance(stack, list):
            for s in stack:
                s2 = _safe_str(s)
                if s2 and s2 not in raw_skills:
                    raw_skills.append(s2)

    # project_signals
    project_signals = _find_project_signals(description, title)

    # interview_themes
    interview_themes = INTERVIEW_THEMES_BY_DIRECTION.get(
        direction.split("、")[0] if "、" in direction else direction,
        ["项目深挖", "技术基础", "业务理解"],
    )

    # source
    source = _safe_str(raw.get("source", "public"))
    source_url = _safe_str(raw.get("url", "") or raw.get("apply_url", "")
                           or raw.get("source_url", ""))

    # posted_at
    posted_at = _safe_str(raw.get("posted_at", "") or raw.get("created_at", "")
                          or raw.get("date", "") or "未知")

    # quality score
    quality = _quality_score(title, description, direction, raw_skills)

    # 生成稳定的 id
    dedup_key = f"{title}|{company}|{city}"
    job_id = hashlib.md5(dedup_key.encode()).hexdigest()[:12]

    return {
        "id": job_id,
        "title": title,
        "company": company,
        "city": city,
        "stage": stage,
        "direction": direction,
        "skills": raw_skills,
        "project_signals": project_signals,
        "jd": description,
        "interview_themes": interview_themes,
        "source": source,
        "source_url": source_url,
        "posted_at": posted_at,
        "data_quality_score": quality,
    }


def infer_direction(title: str, description: str, skills: list[str] | None = None) -> str:
    """根据标题和描述推断岗位方向。"""
    text = f"{title} {description}".lower()
    scores: dict[str, int] = {}

    for direction, keywords in DIRECTION_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text)
        if count > 0:
            scores[direction] = count

    if not scores:
        return "通用技术"

    # 取最高分的 1-2 个方向
    sorted_dirs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_dirs) >= 2 and sorted_dirs[1][1] >= sorted_dirs[0][1] * 0.6:
        return f"{sorted_dirs[0][0]}/{sorted_dirs[1][0]}"
    return sorted_dirs[0][0]


def infer_stage(title: str, seniority: str = "", employment_type: str = "") -> str:
    """推断岗位阶段（实习/校招/社招/不限）。"""
    text = f"{title} {seniority} {employment_type}".lower()

    for stage, keywords in STAGE_KEYWORDS.items():
        if stage == "不限":
            continue
        for kw in keywords:
            if kw in text:
                return stage

    if "实习" in title or "intern" in title.lower():
        return "实习"
    if "校招" in title or "应届" in title:
        return "校招"

    return "不限"


def _find_skills(text: str) -> list[str]:
    """从文本中提取技能关键词。"""
    found = set()
    for match in SKILL_PATTERN.finditer(text.lower()):
        skill = match.group(0).lower()
        # 标准化部分技能名
        skill = skill.replace(" ", "").replace("-", ".").replace("_", ".")
        found.add(skill)
    return sorted(found)


def _find_project_signals(description: str, title: str) -> list[str]:
    """从描述中提取项目信号。"""
    text = f"{title} {description}".lower()
    signals = []
    for signal, keywords in PROJECT_SIGNALS.items():
        if any(kw.lower() in text for kw in keywords):
            signals.append(signal)
    return signals


def _infer_city(location: str) -> str:
    """从位置字符串提取城市名。"""
    if not location:
        return "不限"
    cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "南京", "武汉", "西安", "苏州",
              "天津", "重庆", "长沙", "合肥", "郑州", "厦门", "青岛", "大连", "济南",
              "Remote", "remote", "远程"]
    for c in cities:
        if c.lower() in location.lower():
            return c
    # 尝试从英文地点提取
    eng_cities = {
        "san francisco": "旧金山", "new york": "纽约", "seattle": "西雅图",
        "london": "伦敦", "berlin": "柏林", "singapore": "新加坡", "tokyo": "东京",
        "toronto": "多伦多", "vancouver": "温哥华", "bay area": "旧金山湾区",
    }
    for eng, cn in eng_cities.items():
        if eng in location.lower():
            return cn
    return location[:20]


def _quality_score(title: str, description: str, direction: str, skills: list[str]) -> int:
    """数据质量评分 (0-100)。"""
    score = 60  # 基础分

    if len(title) >= 5:
        score += 10
    if len(description) >= 100:
        score += 10
    if direction != "通用技术":
        score += 10
    if len(skills) >= 3:
        score += 10
    if len(description) >= 300:
        score += 5
    if len(title) >= 10:
        score += 5

    return min(100, max(0, score))


def deduplicate_jobs(jobs: list[dict], key_fields: tuple = ("title", "company", "city")) -> list[dict]:
    """基于指定字段去重，保留第一条。"""
    seen: set = set()
    result = []
    for job in jobs:
        key = tuple(_safe_str(job.get(f, "")) for f in key_fields)
        if key not in seen:
            seen.add(key)
            result.append(job)
    return result


def merge_jobs(builtin_jobs: list[dict], public_jobs: list[dict]) -> list[dict]:
    """合并内置岗位与公开岗位，去重，内置优先。"""
    merged = list(builtin_jobs)
    builtin_keys = {
        (_safe_str(j.get("title", "")), _safe_str(j.get("company", "")), _safe_str(j.get("city", "")))
        for j in builtin_jobs
    }
    for pj in public_jobs:
        key = (_safe_str(pj.get("title", "")), _safe_str(pj.get("company", "")), _safe_str(pj.get("city", "")))
        if key not in builtin_keys:
            merged.append(pj)
            builtin_keys.add(key)
    return merged


def _safe_str(val: Any) -> str:
    """安全转为字符串。"""
    if val is None:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list):
        return ", ".join(_safe_str(v) for v in val if v)
    return str(val).strip()
