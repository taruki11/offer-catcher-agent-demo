"""
Strict smoke test for src.semantic_retriever.

This test is meant to run on the 3060 machine with the pytorch123 env.
It uses cached models only and fails loudly when semantic recall returns
empty results or misses the expected Top1 job.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = PROJECT_ROOT / "data" / "jobs_corpus.json"
MERGED_PATH = PROJECT_ROOT / "data" / "jobs_merged.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TEST_CASES = [
    {
        "name": "llm_rag_agent",
        "resume_text": """
        硕士在读，熟悉 Python、PyTorch、Transformer、RAG、Agent。
        项目经历包括 GenAdRec 生成式广告推荐、LLM 求职助手 Demo，
        使用 RAG、Agent、Embedding、Prompt Engineering、LangChain、FAISS。
        求职方向：大模型应用算法、RAG 工程师、Agent 应用开发。
        """,
        "target_role": "大模型应用算法",
        "expected_top1_any": ["大模型应用算法实习生", "大模型算法实习生"],
    },
    {
        "name": "recommendation",
        "resume_text": """
        熟悉 Python、TensorFlow、推荐系统、CTR 预估、协同过滤。
        做过电商推荐系统、DeepFM、DIN、广告 CTR 预估、DeepCTR。
        技能包括推荐算法、深度学习、Spark、Hive、SQL、特征工程。
        求职方向：推荐算法工程师、广告算法。
        """,
        "target_role": "推荐算法",
        "expected_top1_any": ["推荐系统工程师"],
    },
    {
        "name": "computer_vision",
        "resume_text": """
        熟悉 Python、PyTorch、计算机视觉、目标检测、图像分类。
        做过 YOLOv8 小目标检测、ImageNet 图像分类、ViT 实验。
        技能包括 CV、目标检测、图像分割、PyTorch、OpenCV、Transformer、ViT。
        求职方向：计算机视觉算法工程师。
        """,
        "target_role": "计算机视觉",
        "expected_top1_any": ["计算机视觉算法实习生"],
    },
]


def _prepare_corpus() -> None:
    if CORPUS_PATH.exists():
        return
    if not MERGED_PATH.exists():
        raise FileNotFoundError(f"Missing corpus files: {CORPUS_PATH} and {MERGED_PATH}")
    CORPUS_PATH.write_text(MERGED_PATH.read_text(encoding="utf-8"), encoding="utf-8")


def _assert_corpus_size() -> None:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    if not isinstance(corpus, list) or len(corpus) < 500:
        raise AssertionError(f"jobs_corpus.json must contain >=500 jobs, got {len(corpus) if isinstance(corpus, list) else 'invalid'}")


def _write_report(results_all: list[dict]) -> None:
    report_path = PROJECT_ROOT / "reports" / "semantic_retriever_smoke.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Semantic Retriever Smoke Test Report",
        "",
        "**Model**: `sentence-transformers/all-MiniLM-L6-v2` or `SEMANTIC_MODEL_PATH` override",
        "",
        "**Mode**: read-only cached embedding model + FAISS, no LLM API, no training.",
        "",
        "| Case | Expected Top1 Contains | Actual Top1 | Score | Status |",
        "|------|------------------------|-------------|-------|--------|",
    ]
    for item in results_all:
        lines.append(
            f"| {item['case']} | {item['expected']} | {item['actual']} | {item['score']:.4f} | {item['status']} |"
        )
    lines.append("")
    lines.append("## Top5 Details")
    lines.append("")
    for item in results_all:
        lines.append(f"### {item['case']}")
        for row in item["top5"]:
            lines.append(f"- {row['rank']}. {row['title']} ({row['semantic_score']:.4f})")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[REPORT] {report_path}")


def main() -> int:
    _prepare_corpus()
    _assert_corpus_size()

    from src.semantic_retriever import is_available, query

    if not is_available():
        print("[FAIL] semantic retriever is not available")
        return 2

    results_all: list[dict] = []
    failures: list[str] = []

    for case in TEST_CASES:
        results = query(
            resume_text=case["resume_text"],
            target_role=case["target_role"],
            corpus_path=str(CORPUS_PATH),
            top_k=5,
        )
        if not results:
            failures.append(f"{case['name']}: empty results")
            continue
        if not all("semantic_score" in item for item in results):
            failures.append(f"{case['name']}: missing semantic_score")
            continue

        top1 = results[0]
        top1_title = str(top1.get("title", ""))
        expected_any = case["expected_top1_any"]
        status = "PASS" if any(expected in top1_title for expected in expected_any) else "FAIL"
        if status != "PASS":
            failures.append(f"{case['name']}: expected Top1 contains one of {expected_any}, got {top1_title}")

        top5 = [
            {
                "rank": idx,
                "title": str(item.get("title", "")),
                "semantic_score": float(item.get("semantic_score", 0.0)),
            }
            for idx, item in enumerate(results[:5], start=1)
        ]
        results_all.append(
            {
                "case": case["name"],
                "expected": " / ".join(expected_any),
                "actual": top1_title,
                "score": float(top1.get("semantic_score", 0.0)),
                "status": status,
                "top5": top5,
            }
        )
        print(f"[{status}] {case['name']}: Top1={top1_title} score={top1.get('semantic_score')}")

    _write_report(results_all)

    if failures:
        print("[FAIL] semantic smoke failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("SEMANTIC_RETRIEVER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
