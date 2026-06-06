"""
Corpus Eval: 评估大库下检索质量。

Usage:
  python scripts/eval_corpus_quality.py

Outputs:
  reports/corpus_eval_report.md
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.matcher import rank_job_list
from src.resume_parser import parse_resume


# 6-8 个代表性简历和目标方向
TEST_QUERIES = [
    {
        "name": "CV 学生（目标：计算机视觉）",
        "resume": """张伟
计算机视觉方向硕士生
技能：PyTorch, ResNet, YOLO, OpenCV, Python, 目标检测, 图像分类
项目：
1. 基于 YOLOv8 的实时目标检测系统（mAP 0.68）
2. 细粒度图像分类（ResNet + 注意力机制，Top1 准确率 89%）
""",
        "target_role": "计算机视觉",
        "target_city": "北京",
        "stage": "实习",
    },
    {
        "name": "LLM Agent 学生（目标：大模型应用算法）",
        "resume": """李明
大模型应用算法方向
技能：Python, PyTorch, LangChain, RAG, Agent, LLM, Embedding, Prompt
项目：
1. 基于 RAG 的知识库问答系统（召回率 85%，准确率 78%）
2. 多 Agent 协作任务规划框架（成功率达 72%）
""",
        "target_role": "大模型应用算法",
        "target_city": "深圳",
        "stage": "实习",
    },
    {
        "name": "推荐算法学生（目标：推荐算法）",
        "resume": """王芳
推荐算法方向
技能：Python, PyTorch, 推荐系统, 召回, 排序, NDCG, A/B Test, Embedding
项目：
1. 短视频推荐召回排序优化（线上 CTR + 12%）
2. 多目标推荐优化（CTR + CVR 联合优化）
""",
        "target_role": "推荐算法",
        "target_city": "北京",
        "stage": "校招",
    },
    {
        "name": "后端开发（目标：后端研发）",
        "resume": """赵强
后端研发方向
技能：Go, Python, Docker, Kubernetes, MySQL, Redis, FastAPI, 微服务
项目：
1. 高并发订单系统（QPS 5000+，P99 延迟 < 50ms）
2. 微服务治理平台（服务发现、熔断、限流）
""",
        "target_role": "后端研发",
        "target_city": "上海",
        "stage": "校招",
    },
    {
        "name": "数据分析（目标：数据分析）",
        "resume": """陈静
数据分析方向
技能：Python, SQL, Pandas, A/B Test, 指标体系, 可视化, Hive
项目：
1. 用户增长漏斗分析（识别 3 个关键流失点，转化率 + 18%）
2. A/B 实验平台搭建（支持 50+ 并行实验）
""",
        "target_role": "数据分析",
        "target_city": "杭州",
        "stage": "实习",
    },
    {
        "name": "NLP 转 LLM（目标：大模型应用算法）",
        "resume": """王磊
NLP 转大模型应用算法
技能：Python, PyTorch, BERT, 文本分类, 命名实体识别, LLM, Prompt
项目：
1. 基于 BERT 的文本分类系统（准确率 92%）
2. 命名实体识别模型（F1 值 0.87）
3. 正在学习 RAG 和 Agent，有一个简单的 demo
""",
        "target_role": "大模型应用算法",
        "target_city": "北京",
        "stage": "实习",
    },
    {
        "name": "弱项目背景（目标：推荐算法）",
        "resume": """刘洋
推荐算法方向
技能：Python, 机器学习, 数据分析
项目：
1. 课程作业：MovieLens 推荐系统（协同过滤）
2. 无实习经历，无论文发表
""",
        "target_role": "推荐算法",
        "target_city": "上海",
        "stage": "校招",
    },
]


def load_corpus() -> list[dict]:
    corpus_path = ROOT / "data" / "jobs_corpus.json"
    if not corpus_path.exists():
        print(f"[FAIL] {corpus_path} not found")
        return []
    with corpus_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def check_topk(jobs: list[dict], query: dict, k: int = 5) -> dict:
    """检查 TopK 检索质量。"""
    profile = parse_resume(query["resume"])
    profile["_target_role"] = query["target_role"]
    profile["_city"] = query["target_city"]
    profile["_stage"] = query["stage"]

    start = time.time()
    ranked = rank_job_list(
        resume_text=query["resume"],
        profile=profile,
        target_role=query["target_role"],
        target_city=query["target_city"],
        stage=query["stage"],
        top_k=k,
        jobs=jobs,
    )
    elapsed = time.time() - start

    topk = ranked[:k]

    # 1. direction 命中
    direction_hit = sum(
        1 for j in topk if query["target_role"] in (j.get("direction") or "")
    )
    direction_recall = direction_hit / max(k, 1)

    # 2. city / stage 合理性
    city_hit = sum(
        1 for j in topk
        if j.get("city") == query["target_city"] or j.get("city") == "不限"
    )
    stage_hit = sum(
        1 for j in topk
        if j.get("stage") == query["stage"] or j.get("stage") == "不限"
    )

    # 3. 重复标题
    titles = [j.get("title", "") for j in topk]
    duplicate = k - len(set(titles))
    duplicate_ratio = duplicate / max(k, 1)

    # 4. 空字段
    empty_skills = sum(1 for j in topk if not j.get("skills"))
    empty_jd = sum(1 for j in topk if not j.get("jd") and not j.get("description"))

    # 5. source 多样性
    sources = [j.get("source", "unknown") for j in topk]
    source_counter = Counter(sources)
    top_source, top_source_count = source_counter.most_common(1)[0]
    source_diversity = 1.0 - (top_source_count / max(k, 1))

    # 6. 提取打分字段
    topk_detail = []
    for j in topk:
        topk_detail.append({
            "title": j.get("title", "?"),
            "company": j.get("company", "?"),
            "city": j.get("city", "?"),
            "direction": j.get("direction", "?"),
            "source": j.get("source", "?"),
            "match_score": j.get("match_score", "?"),
            "apply_priority": j.get("apply_priority", "?"),
            "pass_score": j.get("pass_score", "?"),
            "risk_score": j.get("risk_score", "?"),
        })

    return {
        "query_name": query["name"],
        "target_role": query["target_role"],
        "elapsed": round(elapsed, 3),
        "topk_detail": topk_detail,
        "direction_hit": direction_hit,
        "direction_recall": direction_recall,
        "city_hit": city_hit,
        "stage_hit": stage_hit,
        "duplicate": duplicate,
        "duplicate_ratio": duplicate_ratio,
        "empty_skills": empty_skills,
        "empty_jd": empty_jd,
        "source_diversity": source_diversity,
        "top_source": top_source,
    }


def generate_report(results: list[dict]) -> str:
    lines = []
    lines.append("# Corpus Eval Report\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Corpus**: `data/jobs_corpus.json`\n")
    lines.append(f"**Queries**: {len(results)}\n")

    # 汇总指标
    total_direction_hit = sum(r["direction_hit"] for r in results)
    total_empty = sum(r["empty_skills"] + r["empty_jd"] for r in results)
    avg_diversity = sum(r["source_diversity"] for r in results) / max(len(results), 1)

    lines.append("## 汇总指标\n")
    lines.append(f"- **Top1 方向命中率**: {total_direction_hit}/{len(results)} ({total_direction_hit/max(len(results),1)*100:.1f}%)\n")
    lines.append(f"- **Top5 方向召回率**: 见各 case\n")
    lines.append(f"- **空字段数**: {total_empty}\n")
    lines.append(f"- **平均来源多样性**: {avg_diversity*100:.1f}%\n")

    # 每个 query 的 Top5 表格
    for r in results:
        lines.append(f"## {r['query_name']}\n")
        lines.append(f"- **Target**: {r['target_role']}\n")
        lines.append(f"- **Elapsed**: {r['elapsed']}s\n")
        lines.append(f"- **Direction Hit**: {r['direction_hit']}/5 ({r['direction_recall']*100:.1f}%)\n")
        lines.append(f"- **City Hit**: {r['city_hit']}/5\n")
        lines.append(f"- **Stage Hit**: {r['stage_hit']}/5\n")
        lines.append(f"- **Duplicate Titles**: {r['duplicate']}/5 ({r['duplicate_ratio']*100:.1f}%)\n")
        lines.append(f"- **Empty Skills**: {r['empty_skills']}\n")
        lines.append(f"- **Empty JD**: {r['empty_jd']}\n")
        lines.append(f"- **Source Diversity**: {r['source_diversity']*100:.1f}% (top: {r['top_source']})\n")

        lines.append("\n**Top 5 Results**:\n\n")
        lines.append("| Rank | Title | Company | Direction | City | Source | Match | Priority | Pass | Risk |\n")
        lines.append("|---|---|---|---|---|---|---|---|---|---|\n")
        for i, job in enumerate(r["topk_detail"]):
            lines.append(
                f"| {i+1} | {job['title']} | {job['company']} "
                f"| {job['direction']} | {job['city']} | {job['source']} "
                f"| {job['match_score']} | {job['apply_priority']} "
                f"| {job['pass_score']} | {job['risk_score']} |\n"
            )
        lines.append("\n")

    # 建议
    lines.append("## 建议\n")
    if total_empty > 0:
        lines.append("- [WARN] 发现空字段，检查数据源。\n")
    if avg_diversity < 0.4:
        lines.append("- [WARN] 来源多样性低，增加真实公开数据。\n")
    lines.append("\n---\n")
    lines.append("*Report generated by `scripts/eval_corpus_quality.py`*\n")

    return "".join(lines)


def main() -> None:
    print("[INFO] Loading job corpus...")
    jobs = load_corpus()
    if not jobs:
        return

    print(f"[INFO] Loaded {len(jobs)} jobs. Running corpus eval...")

    results = []
    for query in TEST_QUERIES:
        print(f"[INFO] Query: {query['name']}")
        result = check_topk(jobs, query, k=5)
        results.append(result)

    print("[INFO] Generating report...")
    report = generate_report(results)

    output_path = ROOT / "reports" / "corpus_eval_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"[OK] Report saved to {output_path}")
    print(f"[SUMMARY] Queries: {len(results)}, Empty Fields: {sum(r['empty_skills'] + r['empty_jd'] for r in results)}")


if __name__ == "__main__":
    main()
