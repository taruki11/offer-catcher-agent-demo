"""
test_data_ingestion.py — 测试公开岗位数据接入管线

使用内置 30 条模拟公开岗位样本，测试 normalize、filter、deduplicate、merge 全链路。
可离线运行，不依赖网络。
输出 data/public_jobs_sample.json 和 data/jobs_merged.json。
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.public_job_ingestion import (
    normalize_public_job,
    infer_direction,
    infer_stage,
    _find_skills,
    _quality_score,
    deduplicate_jobs,
    merge_jobs,
    _safe_str,
)

# ---------------------------------------------------------------------------
# 内置 30 条模拟公开岗位样本（覆盖 AI/ML/LLM/Agent/推荐/后端/CV/NLP/数据分析）
# ---------------------------------------------------------------------------

FIXTURE_JOBS = [
    # ----- LLM / Agent 方向 (8 条) -----
    {"title": "LLM Application Engineer Intern", "company": "Anthropic", "location": "San Francisco",
     "description": "Build LLM-powered applications using Claude API. Implement RAG pipelines and agent workflows. Requirements: Python, PyTorch, LangChain, experience with prompt engineering and vector databases.",
     "employment_type": "Internship", "source": "greenhouse"},
    {"title": "大模型算法实习生", "company": "字节跳动", "location": "北京",
     "description": "负责大模型应用算法研发，包括 RAG 检索增强、Agent 工具调用、Prompt 优化。要求熟悉 Python、PyTorch、Transformer，有 LLM 项目经验优先。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "AI Research Scientist - LLM", "company": "Meta", "location": "Menlo Park",
     "description": "Research and develop large language models. Fine-tune models using LoRA/QLoRA. Build evaluation benchmarks. Requirements: PhD in CS/NLP, publications at top venues.",
     "employment_type": "Full-time", "source": "lever"},
    {"title": "Generative AI Engineer", "company": "Stability AI", "location": "London",
     "description": "Develop generative AI applications with diffusion models and LLMs. Build RAG systems for document understanding. Requirements: Python, PyTorch, HuggingFace, LangChain.",
     "employment_type": "Full-time", "source": "ashby"},
    {"title": "Agent 应用开发工程师", "company": "Minimax", "location": "上海",
     "description": "开发基于 LLM 的 Agent 应用，实现多轮对话和工具调用。要求熟悉 LangChain Agent 框架，有 Function Calling 实践，了解 ReAct 工作流。",
     "employment_type": "社招", "source": "fixture"},
    {"title": "NLP 算法实习生（大模型方向）", "company": "百度", "location": "北京",
     "description": "参与文心大模型应用开发，进行 NER/文本分类/摘要等任务微调。要求：Python, PyTorch, BERT, HuggingFace Transformers，有 NLP 项目经验。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "LLM Infrastructure Engineer", "company": "OpenAI", "location": "San Francisco",
     "description": "Build scalable infrastructure for training and serving large language models. Optimize inference latency. Requirements: Python, CUDA, Triton, Ray, Kubernetes.",
     "employment_type": "Full-time", "source": "greenhouse"},
    {"title": "AI Application Developer", "company": "Notion", "location": "San Francisco",
     "description": "Integrate AI features into Notion's product using LLMs. Build RAG-powered Q&A, summarization, and writing assistants. Requirements: TypeScript, Python, API design.",
     "employment_type": "Full-time", "source": "lever"},

    # ----- 推荐算法方向 (5 条) -----
    {"title": "推荐算法实习生", "company": "快手", "location": "北京",
     "description": "参与短视频推荐排序模型优化，包括召回、粗排、精排。要求熟悉推荐系统、排序模型、NDCG指标体系。Python、PyTorch、A/B Test 经验优先。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "Machine Learning Engineer - Recommendations", "company": "Spotify", "location": "Stockholm",
     "description": "Build recommendation systems for music discovery. Work on collaborative filtering, content-based recommendations, and multi-objective ranking. Requirements: Python, TensorFlow, Scala.",
     "employment_type": "Full-time", "source": "greenhouse"},
    {"title": "搜索推荐算法工程师", "company": "阿里巴巴", "location": "杭州",
     "description": "负责电商搜索和推荐算法优化，提升 CTR/CVR。要求掌握排序模型(LTR/DNN)、召回策略、多目标优化。Python、TensorFlow 熟练。",
     "employment_type": "社招", "source": "fixture"},
    {"title": "推荐系统工程师", "company": "美团", "location": "北京",
     "description": "优化外卖推荐系统，从召回-粗排-精排全链路优化。要求熟悉 Wide&Deep、DeepFM、多任务学习。Python、Spark、Hive 熟练。",
     "employment_type": "社招", "source": "fixture"},
    {"title": "Junior Data Scientist - RecSys", "company": "Delivery Hero", "location": "Berlin",
     "description": "Develop recommendation models for food delivery. Apply collaborative filtering and deep learning to improve order recommendations. Requirements: Python, SQL, basic ML.",
     "employment_type": "Entry Level", "source": "ashby"},

    # ----- 后端/AI平台方向 (5 条) -----
    {"title": "后端研发实习生（Go 方向）", "company": "腾讯", "location": "深圳",
     "description": "参与 AI 平台后端服务开发，使用 Go 语言。要求掌握 Go、MySQL、Redis、消息队列，了解微服务架构和 gRPC。有分布式系统经验优先。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "Backend Engineer - AI Platform", "company": "Stripe", "location": "Seattle",
     "description": "Build backend services for Stripe's ML platform. Design APIs for model serving and feature store. Requirements: Go/Java, gRPC, Kubernetes, experience with ML infrastructure.",
     "employment_type": "Full-time", "source": "lever"},
    {"title": "云原生后端开发工程师", "company": "华为", "location": "深圳",
     "description": "开发云原生 AI 平台后端服务，基于 Kubernetes/Docker 构建。要求 Go/Java/Python，熟悉微服务、容器化部署，了解 CI/CD 流程。",
     "employment_type": "社招", "source": "fixture"},
    {"title": "ML Platform Engineer", "company": "Databricks", "location": "San Francisco",
     "description": "Build the platform that powers ML training and serving at scale. Design model registry, feature store, and experiment tracking. Requirements: Python, Scala, K8s, Spark.",
     "employment_type": "Full-time", "source": "greenhouse"},
    {"title": "推荐平台后端实习生", "company": "小红书", "location": "上海",
     "description": "参与推荐平台后端开发，负责特征抽取服务和模型推理引擎。要求 Python/Go、gRPC、Docker，了解推荐系统架构。",
     "employment_type": "实习", "source": "fixture"},

    # ----- CV方向 (3 条) -----
    {"title": "计算机视觉算法实习生（检测方向）", "company": "商汤科技", "location": "上海",
     "description": "参与目标检测和图像分割算法研发，使用 YOLO/DETR/MaskRCNN 等模型。要求 Python、PyTorch、OpenCV，有 CV 项目经验优先。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "Computer Vision Engineer", "company": "Tesla", "location": "Palo Alto",
     "description": "Develop computer vision algorithms for autonomous driving. Work on object detection, lane detection, and scene understanding. Requirements: Python, PyTorch, OpenCV.",
     "employment_type": "Full-time", "source": "lever"},
    {"title": "图像识别算法实习生", "company": "旷视科技", "location": "北京",
     "description": "参与图像分类、OCR 识别算法研发。要求 Python、PyTorch、CNN/ResNet/ViT 等模型经验，有模型轻量化和部署经验优先。",
     "employment_type": "实习", "source": "fixture"},

    # ----- NLP方向 (3 条) -----
    {"title": "NLP Research Intern", "company": "Google", "location": "Mountain View",
     "description": "Research in natural language processing. Work on multilingual models, text generation, and dialogue systems. Requirements: PyTorch, HuggingFace, publications.",
     "employment_type": "Internship", "source": "greenhouse"},
    {"title": "搜索 NLP 算法实习生", "company": "搜狗", "location": "北京",
     "description": "参与搜索 Query 理解和排序优化，包括意图识别、Query 纠错改写。要求 NLP 基础，Python，PyTorch/BERT，有搜索/对话系统项目优先。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "文本生成算法工程师", "company": "阅文集团", "location": "上海",
     "description": "负责网络文学 AI 创作和文本生成模型优化。要求 NLP 背景，熟悉 GPT/BART 等生成式模型，有模型微调和部署经验。",
     "employment_type": "社招", "source": "fixture"},

    # ----- 数据分析方向 (3 条) -----
    {"title": "校招数据分析实习生", "company": "滴滴出行", "location": "北京",
     "description": "参与出行平台数据分析，设计指标体系、构建用户画像。要求 SQL 熟练，Python 数据分析，有 A/B 实验和可视化经验优先。",
     "employment_type": "校招", "source": "fixture"},
    {"title": "推荐数据分析实习生", "company": "Bilibili", "location": "上海",
     "description": "分析视频推荐效果指标，包括 CTR/CVR/用户停留时长。要求 SQL/Python 数据分析，了解推荐系统指标体系，有 Hadoop/Spark 经验优先。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "Data Analyst - Growth", "company": "Canva", "location": "Sydney",
     "description": "Analyze user growth metrics and build dashboards. Design A/B tests and measure impact of product changes. Requirements: SQL, Python/R, Tableau.",
     "employment_type": "Full-time", "source": "lever"},

    # ----- 搜索方向 (2 条) -----
    {"title": "智能搜索算法实习生", "company": "知乎", "location": "北京",
     "description": "优化知乎内容搜索排序，包括向量检索、文本相关性排序。要求 NLP/搜索背景，Python/PyTorch，了解 ES/向量数据库。",
     "employment_type": "实习", "source": "fixture"},
    {"title": "校招人岗匹配算法实习生", "company": "BOSS直聘", "location": "北京",
     "description": "参与人岗匹配算法研发，包括简历-岗位语义匹配、Embedding 召回、排序模型优化。要求 NLP/推荐系统背景，有向量检索和排序项目经验。",
     "employment_type": "校招", "source": "fixture"},

    # ----- 游戏AI/其他方向 (1 条) -----
    {"title": "游戏 AI 算法实习生", "company": "网易游戏", "location": "广州",
     "description": "参与游戏 AI 研发，包括 NPC 行为决策、强化学习训练。要求 Python、PyTorch、强化学习基础，有游戏 AI 项目经验优先。",
     "employment_type": "实习", "source": "fixture"},
]


# ---------------------------------------------------------------------------
# 测试函数
# ---------------------------------------------------------------------------

def test_normalize():
    """测试 normalize_public_job 对每条 fixture 输出合法 schema。"""
    print("[TEST] normalize_public_job ...")
    required_fields = ["id", "title", "company", "city", "stage", "direction",
                       "skills", "project_signals", "jd", "interview_themes",
                       "source", "source_url", "posted_at", "data_quality_score"]
    passed = 0
    failed = 0
    for i, raw in enumerate(FIXTURE_JOBS):
        job = normalize_public_job(raw)
        if job is None:
            print(f"  [WARN] fixture[{i}] returned None")
            failed += 1
            continue
        missing = [f for f in required_fields if f not in job]
        if missing:
            print(f"  [FAIL] fixture[{i}] '{job.get('title', '?')}' missing fields: {missing}")
            failed += 1
        else:
            passed += 1

    ok = passed > 0 and failed == 0
    print(f"  [{'PASS' if ok else 'FAIL'}] normalize: {passed} passed, {failed} failed")


def test_direction():
    """测试方向推断。"""
    print("[TEST] infer_direction ...")
    cases = [
        ("大模型应用算法实习生", "负责 LLM 应用开发，包括 RAG 和 Agent 工作流。", "LLM"),
        ("推荐算法实习生", "优化推荐排序模型，提升 CTR 和 NDCG。", "推荐算法"),
        ("计算机视觉算法实习生", "使用 YOLO 进行目标检测和图像分割。", "计算机视觉"),
        ("后端研发实习生", "开发 Go 微服务，使用 gRPC 和 K8s。", "后端开发"),
        ("数据分析实习生", "分析用户数据，设计指标体系。", "数据分析"),
    ]
    passed = 0
    for title, desc, expected_dir in cases:
        direction = infer_direction(title, desc)
        if expected_dir in direction:
            passed += 1
        else:
            print(f"  [WARN] '{title}' -> '{direction}', expected '{expected_dir}'")
    ok = passed >= 4
    print(f"  [{'PASS' if ok else 'FAIL'}] direction infer: {passed}/{len(cases)}")


def test_skills():
    """测试技能提取。"""
    print("[TEST] _find_skills ...")
    desc = ("Requirements: Python, PyTorch, LangChain, FAISS, Docker. "
            "Experience with RAG and Agent workflows. Knowledge of BERT, GPT, and Transformers.")
    skills = _find_skills(desc)
    expected_subset = ["python", "pytorch", "langchain", "faiss", "docker", "bert", "gpt"]
    hits = sum(1 for s in expected_subset if s in skills)
    ok = hits >= 5
    print(f"  [{'PASS' if ok else 'FAIL'}] Found {len(skills)} skills, {hits}/{len(expected_subset)} expected present")


def test_quality():
    """测试质量评分。"""
    print("[TEST] _quality_score ...")
    s1 = _quality_score("LLM Engineer", "Short desc.", "LLM", ["python"])
    s2 = _quality_score("大模型应用算法实习生", "这是一段很详细的岗位描述，" * 10, "LLM",
                        ["python", "pytorch", "langchain", "faiss"])
    ok = s2 > s1
    print(f"  [{'PASS' if ok else 'FAIL'}] short JD score={s1}, long JD score={s2}")


def test_dedup_move():
    """测试去重。"""
    print("[TEST] deduplicate_jobs ...")
    jobs = [
        {"title": "A", "company": "X", "city": "北京"},
        {"title": "A", "company": "X", "city": "北京"},
        {"title": "B", "company": "Y", "city": "上海"},
    ]
    result = deduplicate_jobs(jobs)
    ok = len(result) == 2
    print(f"  [{'PASS' if ok else 'FAIL'}] dedup: {len(jobs)} -> {len(result)}")


def test_merge():
    """测试合并。"""
    print("[TEST] merge_jobs ...")
    builtin = [
        {"title": "大模型应用算法实习生", "company": "字节跳动", "city": "北京"},
        {"title": "推荐算法实习生", "company": "快手", "city": "北京"},
    ]
    public = [
        {"title": "LLM Engineer", "company": "OpenAI", "city": "SF"},
        {"title": "大模型应用算法实习生", "company": "字节跳动", "city": "北京"},  # 重复
    ]
    merged = merge_jobs(builtin, public)
    ok = len(merged) == 3
    print(f"  [{'PASS' if ok else 'FAIL'}] merge: {len(builtin)}+{len(public)} -> {len(merged)} (dup removed)")


def generate_sample_files():
    """生成非破坏性的测试样例文件，不覆盖正式岗位库。"""
    data_dir = os.path.join(ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 标准化所有 fixture
    normalized = []
    for raw in FIXTURE_JOBS:
        job = normalize_public_job(raw)
        if job:
            normalized.append(job)

    # 去重
    deduped = deduplicate_jobs(normalized)

    # 至少保底取前 30 条（去重后可能少于30）
    sample = deduped[:min(len(deduped), 30)]

    # 保存到 test_* 文件，避免覆盖正式 data/public_jobs_sample.json。
    sample_path = os.path.join(data_dir, "test_public_jobs_sample.json")
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)

    # 合并
    builtin_path = os.path.join(data_dir, "jobs.json")
    if os.path.exists(builtin_path):
        with open(builtin_path, "r", encoding="utf-8") as f:
            builtin = json.load(f)
    else:
        builtin = []

    merged = merge_jobs(builtin, sample)
    merged_path = os.path.join(data_dir, "test_jobs_merged.json")
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"[OK] test_public_jobs_sample.json: {len(sample)} jobs")
    print(f"[OK] test_jobs_merged.json: {len(merged)} jobs (builtin {len(builtin)} + public {len(sample)} = {len(builtin)}+{len(sample)} -> {len(merged)} after dedup)")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  test_data_ingestion.py")
    print("=" * 60)

    test_normalize()
    test_direction()
    test_skills()
    test_quality()
    test_dedup_move()
    test_merge()
    generate_sample_files()

    print("\n[OK] All tests completed.")


if __name__ == "__main__":
    main()
