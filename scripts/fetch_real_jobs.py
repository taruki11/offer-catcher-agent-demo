"""
fetch_real_jobs.py — 从 HuggingFace na-tech-jobs 数据集拉取真实岗位数据
使用 HF datasets-server API，无需安装任何库（只用 urllib + json）。
过滤 AI/ML/Data/Backend 方向，最多保存 300 条。
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.public_job_ingestion import normalize_public_job, deduplicate_jobs, _quality_score

API_BASE = "https://datasets-server.huggingface.co/rows"
DATASET = "arjun10g/na-tech-jobs"
BATCH_SIZE = 100
MAX_JOBS = 500
MAX_BATCHES = 60  # max 6000 rows to scan
START_OFFSET = 0  # 0 for full scan

# 目标角色族（扩展版，覆盖更多变体）
TARGET_FAMILIES = {
    "ai-ml", "ai / ml", "artificial intelligence / machine learning",
    "machine learning", "deep learning", "ml engineering",
    "data-science", "data science", "data engineering", "data analytics",
    "data an", "data en", "business intelligence",
    "software-engineering", "software engineering", "backend",
    "research", "research science", "applied science",
    "nlp", "computer vision", "robotics",
    "devops", "cloud", "platform", "infrastructure",
    "full-stack", "full stack", "frontend",
}

TITLE_KEYWORDS = [
    "ml ", " ai ", "machine learning", "data sci", "data eng",
    "data analyst", "data analy", "backend", "back-end",
    "recommend", "nlp", "llm", "rag", "agent", "search",
    "computer vision", "deep learning", "python develop",
    "software eng", "full stack", "full-stack", "frontend",
    "devops", "platform eng", "infrastructure",
    "research sci", "applied sci", "quantitative",
]


def fetch_batch(offset: int, length: int = BATCH_SIZE) -> list[dict]:
    """从 API 拉取一批数据。"""
    url = f"{API_BASE}?dataset={DATASET}&config=default&split=train&offset={offset}&length={length}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "OfferCatcher/1.0")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return [r["row"] for r in data.get("rows", [])]
    except Exception as e:
        print(f"  [WARN] API error at offset={offset}: {e}")
        return []


def is_target_role(row: dict) -> bool:
    """判断是否为目标角色。"""
    family = (row.get("role_family_extracted") or "").lower()
    if any(t in family for t in TARGET_FAMILIES):
        return True
    # 标题关键词兜底
    title = (row.get("title") or "").lower()
    return any(kw in title for kw in TITLE_KEYWORDS)


def convert_row(row: dict) -> dict | None:
    """将 HF 行转为项目 schema。"""
    tech_stack = row.get("tech_stack")
    if isinstance(tech_stack, list):
        skills = [s for s in tech_stack if isinstance(s, str)]
    else:
        skills = []

    return {
        "id": row.get("id", ""),
        "title": (row.get("title") or "").strip(),
        "company": (row.get("company_name") or "").strip(),
        "city": (row.get("city") or row.get("location_raw") or "").strip(),
        "stage": (row.get("seniority_extracted") or "").strip(),
        "direction": "",
        "skills": skills,
        "project_signals": [],
        "jd": (row.get("description_md") or row.get("title") or "").strip(),
        "interview_themes": [],
        "source": "huggingface:arjun10g/na-tech-jobs",
        "source_url": (row.get("url") or "").strip(),
        "posted_at": (str(row.get("posted_at") or "")).strip(),
        "data_quality_score": 70,
    }


def main():
    print("=" * 60)
    print("  fetch_real_jobs.py — from arjun10g/na-tech-jobs")
    print("=" * 60)

    all_raw = []
    total_scanned = 0

    for batch_idx in range(MAX_BATCHES):
        offset = batch_idx * BATCH_SIZE
        rows = fetch_batch(offset)
        if not rows:
            print(f"  Batch {batch_idx}: empty, stopping.")
            break

        matching = [r for r in rows if is_target_role(r)]
        all_raw.extend(matching)
        total_scanned += len(rows)

        print(f"  Batch {batch_idx}: scanned={len(rows)}, matched={len(matching)}, total_matched={len(all_raw)}")

        if len(all_raw) >= MAX_JOBS:
            break
        time.sleep(0.3)  # 礼貌限速

    print(f"\n  Total scanned: {total_scanned}, matched: {len(all_raw)}")

    if not all_raw:
        print("  [WARN] No matching jobs found. Check API or network.")
        return

    # 限制数量
    all_raw = all_raw[:MAX_JOBS]

    # 转换并标准化
    normalized = []
    for raw in all_raw:
        converted = convert_row(raw)
        if converted:
            job = normalize_public_job(converted)
            if job and job.get("data_quality_score", 0) >= 60:
                normalized.append(job)

    # 去重
    deduped = deduplicate_jobs(normalized)
    print(f"  After normalize+dedup+quality: {len(deduped)} jobs")

    # 生成日期标记
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    deduped = [{**j, "source": f"huggingface:arjun10g/na-tech-jobs@{today}"} for j in deduped]

    # 保存
    out_path = os.path.join(ROOT, "data", "public_jobs_sample.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Saved {len(deduped)} jobs -> {out_path}")

    # 生成合并文件
    builtin_path = os.path.join(ROOT, "data", "jobs.json")
    if os.path.exists(builtin_path):
        with open(builtin_path, "r", encoding="utf-8") as f:
            builtin = json.load(f)
    else:
        builtin = []

    from src.public_job_ingestion import merge_jobs
    merged = merge_jobs(builtin, deduped)
    merged_path = os.path.join(ROOT, "data", "jobs_merged.json")
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"  [OK] jobs_merged.json: {len(merged)} jobs")

    print("\n[OK] Done.")


if __name__ == "__main__":
    main()
