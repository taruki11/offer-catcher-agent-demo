"""
Build a larger job corpus for Offer Catcher.

The script has two layers:
1. Local curated coverage data. These are clearly marked as curated_seed and
   are used to make the demo robust offline.
2. Optional Hugging Face public datasets. Enable with --try-hf when network is
   available. Public rows are normalized through src.public_job_ingestion.

Outputs:
  data/jobs_corpus.json
  data/job_corpus_stats.json
  data/jobs_merged.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.public_job_ingestion import deduplicate_jobs, merge_jobs, normalize_public_job


COMPANIES = [
    "云智能平台公司",
    "内容推荐平台",
    "社交产品平台",
    "游戏科技平台",
    "金融科技平台",
    "智能出行科技",
    "企业服务云厂商",
    "电商算法平台",
    "本地生活科技",
    "AI 创业公司",
]

CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "南京", "武汉", "西安", "远程"]
STAGES = ["实习", "校招", "不限"]

TEMPLATES = [
    {
        "title": "大模型应用算法工程师",
        "direction": "大模型应用算法",
        "skills": ["Python", "PyTorch", "LLM", "RAG", "Agent", "Embedding", "FAISS", "Prompt"],
        "project_signals": ["RAG", "Agent", "Embedding", "Prompt"],
        "themes": ["RAG 召回与重排", "Agent 工具调用", "结构化输出评估", "Embedding 质量评估"],
        "jd": "负责大模型应用算法、RAG 检索增强、Agent 工具调用和结构化输出评估，优化问答准确率、召回率和稳定性。",
    },
    {
        "title": "LLM Agent 算法工程师",
        "direction": "大模型应用算法",
        "skills": ["Python", "LangChain", "LangGraph", "Tool Calling", "Function Calling", "LLM", "RAG"],
        "project_signals": ["Agent", "RAG", "Tool Calling"],
        "themes": ["多 Agent 协作", "状态机编排", "失败重试", "工具调用观测"],
        "jd": "建设多 Agent 工作流，负责任务规划、工具路由、状态管理、失败兜底和端到端效果评估。",
    },
    {
        "title": "大模型评估算法工程师",
        "direction": "大模型应用算法",
        "skills": ["Python", "LLM 评估", "Prompt", "A/B Test", "数据分析", "自动化测试"],
        "project_signals": ["LLM Eval", "DataAnalysis"],
        "themes": ["评测集构造", "幻觉检测", "自动化打分", "错误归因"],
        "jd": "设计大模型评估体系，构建 golden cases、错误分类、自动化评测脚本和线上质量监控指标。",
    },
    {
        "title": "推荐算法工程师",
        "direction": "推荐算法",
        "skills": ["Python", "PyTorch", "推荐系统", "召回", "排序", "NDCG", "A/B Test", "Embedding"],
        "project_signals": ["Recommendation", "召回", "排序"],
        "themes": ["召回排序链路", "多目标优化", "冷启动", "A/B 实验"],
        "jd": "负责推荐召回、粗排、精排和重排算法优化，关注 CTR、CVR、NDCG、留存等核心指标。",
    },
    {
        "title": "LLM 推荐算法工程师",
        "direction": "推荐算法/大模型应用算法",
        "skills": ["Python", "Transformer", "LLM", "推荐系统", "Semantic ID", "Embedding", "召回", "排序"],
        "project_signals": ["Recommendation", "Embedding", "LLM"],
        "themes": ["LLM4Rec", "Semantic ID", "序列建模", "候选生成"],
        "jd": "探索大模型在推荐系统中的应用，包括语义表征、用户兴趣建模、候选生成和推荐解释生成。",
    },
    {
        "title": "搜索算法工程师",
        "direction": "搜索算法",
        "skills": ["Python", "搜索", "Query 理解", "信息检索", "Embedding", "重排", "NDCG"],
        "project_signals": ["Search", "Embedding"],
        "themes": ["Query 理解", "混合检索", "LTR 排序", "NDCG/MRR"],
        "jd": "负责搜索相关性、Query 理解、召回排序、向量检索和重排模型优化。",
    },
    {
        "title": "NLP 算法工程师",
        "direction": "NLP",
        "skills": ["Python", "PyTorch", "Transformer", "BERT", "NER", "文本分类", "文本生成"],
        "project_signals": ["NLP_Classic", "LLM"],
        "themes": ["Transformer", "NER", "文本分类", "文本生成"],
        "jd": "负责自然语言处理模型训练和应用，包括文本分类、信息抽取、摘要生成、意图识别和生成式模型优化。",
    },
    {
        "title": "计算机视觉算法工程师",
        "direction": "计算机视觉",
        "skills": ["Python", "PyTorch", "OpenCV", "YOLO", "ResNet", "目标检测", "图像分类"],
        "project_signals": ["CV_Traditional"],
        "themes": ["目标检测", "图像分类", "模型部署", "数据增强"],
        "jd": "负责图像分类、目标检测、数据增强、模型压缩和视觉模型部署。",
    },
    {
        "title": "多模态算法工程师",
        "direction": "大模型应用算法/计算机视觉",
        "skills": ["Python", "PyTorch", "CLIP", "多模态", "LLM", "图像理解", "Embedding"],
        "project_signals": ["LLM", "CV_Traditional", "Embedding"],
        "themes": ["多模态对齐", "图文检索", "视觉问答", "数据构造"],
        "jd": "负责图文多模态理解、图文检索、视觉问答和多模态大模型效果评估。",
    },
    {
        "title": "AI 平台后端工程师",
        "direction": "后端研发",
        "skills": ["Python", "Go", "Docker", "Kubernetes", "FastAPI", "Redis", "MySQL", "模型服务"],
        "project_signals": ["Backend", "Deployment"],
        "themes": ["模型服务", "微服务", "容器化部署", "高并发接口"],
        "jd": "负责 AI 平台后端服务、模型推理服务、任务调度、服务治理和监控告警。",
    },
    {
        "title": "机器学习平台工程师",
        "direction": "ML平台/Infra",
        "skills": ["Python", "PyTorch", "Kubernetes", "Triton", "MLflow", "模型部署", "特征存储"],
        "project_signals": ["Deployment", "MLOps"],
        "themes": ["训练平台", "模型服务", "特征平台", "GPU 调度"],
        "jd": "建设机器学习平台，负责训练任务管理、模型服务、特征平台、实验管理和 GPU 资源调度。",
    },
    {
        "title": "数据分析算法工程师",
        "direction": "数据分析",
        "skills": ["Python", "SQL", "Pandas", "A/B Test", "指标体系", "可视化", "Hive"],
        "project_signals": ["DataAnalysis"],
        "themes": ["指标体系", "漏斗分析", "A/B 实验", "SQL 优化"],
        "jd": "负责业务指标体系、用户行为分析、A/B 实验、可视化看板和数据驱动决策支持。",
    },
]

HF_SOURCES = [
    {
        "dataset": "Sundaydream/tech-jobs-dataset-2026",
        "config": "default",
        "split": "train",
        "source": "huggingface:Sundaydream/tech-jobs-dataset-2026",
        "field_map": {
            "title": "title",
            "company": "company",
            "location": "location",
            "description": "description",
            "employment_type": "employment_type",
        },
    },
    {
        "dataset": "batuhanmtl/job-skill-set",
        "config": "default",
        "split": "train",
        "source": "huggingface:batuhanmtl/job-skill-set",
        "field_map": {
            "title": "job_title",
            "description": "job_description",
            "skills": "job_skill_set",
        },
    },
    {
        "dataset": "arjun10g/na-tech-jobs",
        "config": "default",
        "split": "train",
        "source": "huggingface:arjun10g/na-tech-jobs",
        "field_map": {
            "title": "title",
            "company": "company_name",
            "location": "location_raw",
            "description": "description_md",
            "skills": "tech_stack",
            "stage": "seniority_extracted",
            "url": "url",
        },
    },
]


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def build_curated_jobs(target_count: int) -> list[dict]:
    jobs: list[dict] = []
    title_prefixes = ["核心", "平台", "业务", "增长", "评估", "校招", "应用", "基础"]
    idx = 0
    while len(jobs) < target_count:
        template = TEMPLATES[idx % len(TEMPLATES)]
        company = COMPANIES[(idx * 3 + idx // len(TEMPLATES)) % len(COMPANIES)]
        city = CITIES[(idx * 5 + idx // len(COMPANIES)) % len(CITIES)]
        stage = STAGES[(idx + idx // 7) % len(STAGES)]
        prefix = title_prefixes[(idx // len(TEMPLATES)) % len(title_prefixes)]
        title = f"{prefix}{template['title']}（{stage}）"
        raw = {
            "title": title,
            "company": company,
            "location": city,
            "employment_type": stage,
            "description": (
                f"{template['jd']} 工作地点：{city}。阶段：{stage}。"
                f"要求技能：{', '.join(template['skills'])}。"
                f"项目经验信号：{', '.join(template['project_signals'])}。"
                "候选人需要能说明数据、模型、评估指标和上线风险。"
            ),
            "skills": template["skills"],
            "source": "curated_seed:v1",
            "posted_at": "offline-seed",
        }
        job = normalize_public_job(raw)
        if job:
            job["direction"] = template["direction"]
            job["skills"] = template["skills"]
            job["project_signals"] = template["project_signals"]
            job["interview_themes"] = template["themes"]
            job["data_quality_score"] = max(job.get("data_quality_score", 70), 82)
            jobs.append(job)
        idx += 1
    return jobs


def fallback_skills(direction: str) -> list[str]:
    if "大模型" in direction or "LLM" in direction:
        return ["Python", "LLM", "RAG", "Prompt"]
    if "推荐" in direction:
        return ["Python", "推荐系统", "召回", "排序"]
    if "搜索" in direction:
        return ["Python", "搜索", "信息检索", "Embedding"]
    if "视觉" in direction:
        return ["Python", "PyTorch", "OpenCV", "目标检测"]
    if "后端" in direction:
        return ["Go", "Python", "Docker", "MySQL"]
    if "数据" in direction:
        return ["Python", "SQL", "Pandas", "A/B Test"]
    return ["Python", "SQL", "项目经验"]


def fetch_hf_rows(source: dict, limit: int) -> list[dict]:
    rows: list[dict] = []
    dataset = source["dataset"]
    config = source.get("config", "default")
    split = source.get("split", "train")
    encoded = urllib.parse.quote(dataset, safe="")
    for offset in range(0, limit, 100):
        length = min(100, limit - offset)
        url = (
            "https://datasets-server.huggingface.co/rows"
            f"?dataset={encoded}&config={config}&split={split}&offset={offset}&length={length}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "OfferCatcher/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read())
        except Exception as exc:
            print(f"[WARN] HF source failed: {dataset} offset={offset}: {exc}")
            break
        page = [item.get("row", {}) for item in data.get("rows", [])]
        if not page:
            break
        rows.extend(page)
        time.sleep(0.2)
    return rows


def adapt_hf_row(row: dict, source: dict) -> dict:
    field_map = source.get("field_map", {})

    def get(name: str, default: str = ""):
        key = field_map.get(name, name)
        return row.get(key, default)

    skills = get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.replace(";", ",").split(",") if s.strip()]
    elif not isinstance(skills, list):
        skills = []

    return {
        "title": get("title"),
        "company": get("company", "未知公司"),
        "location": get("location"),
        "employment_type": get("employment_type") or get("stage"),
        "description": get("description"),
        "skills": skills,
        "source": source["source"],
        "source_url": get("url"),
        "posted_at": row.get("posted_at") or row.get("date") or "",
    }


def build_stats(jobs: list[dict], output_path: Path) -> dict:
    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_jobs": len(jobs),
        "by_direction": Counter(j.get("direction", "unknown") for j in jobs),
        "by_stage": Counter(j.get("stage", "unknown") for j in jobs),
        "by_source": Counter(j.get("source", "unknown") for j in jobs),
        "avg_quality": round(sum(j.get("data_quality_score", 0) for j in jobs) / max(len(jobs), 1), 2),
    }
    serializable = {
        k: (dict(v) if isinstance(v, Counter) else v)
        for k, v in stats.items()
    }
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    return serializable


def main() -> None:
    parser = argparse.ArgumentParser(description="Build expanded Offer Catcher job corpus")
    parser.add_argument("--target-size", type=int, default=240)
    parser.add_argument("--try-hf", action="store_true", help="Try public Hugging Face datasets")
    parser.add_argument("--hf-limit-per-source", type=int, default=300)
    args = parser.parse_args()

    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    builtin = load_json_list(data_dir / "jobs.json")
    public_sample = load_json_list(data_dir / "public_jobs_sample.json")
    all_public: list[dict] = list(public_sample)

    if args.try_hf:
        for source in HF_SOURCES:
            rows = fetch_hf_rows(source, args.hf_limit_per_source)
            normalized = []
            for row in rows:
                job = normalize_public_job(adapt_hf_row(row, source))
                if job and job.get("data_quality_score", 0) >= 60:
                    normalized.append(job)
            print(f"[INFO] {source['dataset']}: raw={len(rows)} normalized={len(normalized)}")
            all_public.extend(normalized)

    merged = merge_jobs(builtin, deduplicate_jobs(all_public))

    need = max(args.target_size - len(merged), 0)
    if need:
        curated = build_curated_jobs(need)
        merged = merge_jobs(merged, curated)
        print(f"[INFO] Added curated coverage jobs: {len(curated)}")

    corpus = deduplicate_jobs(merged)[: args.target_size]
    for job in corpus:
        if not job.get("skills"):
            job["skills"] = fallback_skills(job.get("direction", ""))
        job.setdefault("source", "unknown")

    corpus_path = data_dir / "jobs_corpus.json"
    merged_path = data_dir / "jobs_merged.json"
    stats_path = data_dir / "job_corpus_stats.json"

    corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    merged_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = build_stats(corpus, stats_path)

    print(f"[OK] jobs_corpus.json: {len(corpus)} jobs")
    print(f"[OK] jobs_merged.json: {len(corpus)} jobs")
    print(f"[OK] job_corpus_stats.json: {stats_path}")
    print("[INFO] by_direction:")
    for direction, count in sorted(stats["by_direction"].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {direction}: {count}")
    print("[INFO] by_source:")
    for source, count in sorted(stats["by_source"].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {source}: {count}")


if __name__ == "__main__":
    main()
