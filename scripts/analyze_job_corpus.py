"""
Analyze job corpus quality and generate report.

Usage:
  python scripts/analyze_job_corpus.py

Outputs:
  reports/job_corpus_analysis.md
"""

from __future__ import annotations

import time
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "jobs_corpus.json"
OUTPUT_PATH = ROOT / "reports" / "job_corpus_analysis.md"


def load_jobs() -> list[dict]:
    if not CORPUS_PATH.exists():
        print(f"[FAIL] {CORPUS_PATH} not found")
        return []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def analyze(jobs: list[dict]) -> dict:
    total = len(jobs)

    # 1. total_jobs
    # 2. by_direction
    directions = [j.get("direction", "unknown") for j in jobs]
    by_direction = Counter(directions)

    # 3. by_stage
    stages = [j.get("stage", "unknown") for j in jobs]
    by_stage = Counter(stages)

    # 4. by_source
    sources = [j.get("source", "unknown") for j in jobs]
    by_source = Counter(sources)

    # 5. empty skills / empty jd / duplicate title ratio
    empty_skills = sum(1 for j in jobs if not j.get("skills"))
    empty_jd = sum(1 for j in jobs if not j.get("jd") and not j.get("description"))
    titles = [j.get("title", "") for j in jobs]
    duplicate_titles = total - len(set(titles))
    duplicate_title_ratio = duplicate_titles / total if total else 0

    # 6. duplicate (title, company, city)
    tc_pairs = [(j.get("title", ""), j.get("company", ""), j.get("city", "")) for j in jobs]
    duplicate_tc = total - len(set(tc_pairs))
    duplicate_tc_ratio = duplicate_tc / total if total else 0

    # 7. top skills
    all_skills = []
    for j in jobs:
        for s in (j.get("skills") or []):
            all_skills.append(s)
    top_skills = Counter(all_skills).most_common(20)

    # 8. avg quality score
    quality_scores = [j.get("data_quality_score", 0) for j in jobs if j.get("data_quality_score")]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    # 9. city coverage
    cities = [j.get("city", "unknown") for j in jobs]
    by_city = Counter(cities)

    # 10. company coverage
    companies = [j.get("company", "unknown") for j in jobs]
    by_company = Counter(companies)

    return {
        "total_jobs": total,
        "by_direction": by_direction,
        "by_stage": by_stage,
        "by_source": by_source,
        "empty_skills": empty_skills,
        "empty_jd": empty_jd,
        "duplicate_titles": duplicate_titles,
        "duplicate_title_ratio": duplicate_title_ratio,
        "duplicate_tc": duplicate_tc,
        "duplicate_tc_ratio": duplicate_tc_ratio,
        "top_skills": top_skills,
        "avg_quality": round(avg_quality, 2),
        "by_city": by_city,
        "by_company": by_company,
    }


def generate_report(stats: dict) -> str:
    lines = []
    lines.append("# Job Corpus Analysis Report\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Corpus Path**: `{CORPUS_PATH}`\n")

    # 1. Total jobs
    lines.append("## 1. Total Jobs\n")
    lines.append(f"- **Total**: {stats['total_jobs']}\n")

    # 2. By Direction
    lines.append("## 2. By Direction\n")
    for direction, count in stats["by_direction"].most_common():
        lines.append(f"- {direction}: {count}\n")

    # 3. By Stage
    lines.append("## 3. By Stage\n")
    for stage, count in stats["by_stage"].most_common():
        lines.append(f"- {stage}: {count}\n")

    # 4. By Source
    lines.append("## 4. By Source\n")
    for source, count in stats["by_source"].most_common():
        lines.append(f"- {source}: {count}\n")

    # 5. Data Quality
    lines.append("## 5. Data Quality\n")
    lines.append(f"- **Empty Skills**: {stats['empty_skills']} ({stats['empty_skills']/stats['total_jobs']*100:.1f}%)\n")
    lines.append(f"- **Empty JD**: {stats['empty_jd']} ({stats['empty_jd']/stats['total_jobs']*100:.1f}%)\n")
    lines.append(f"- **Duplicate Titles**: {stats['duplicate_titles']} ({stats['duplicate_title_ratio']*100:.1f}%)\n")
    lines.append(f"- **Duplicate (Title, Company, City)**: {stats['duplicate_tc']} ({stats['duplicate_tc_ratio']*100:.1f}%)\n")

    # 6. Top Skills
    lines.append("## 6. Top Skills (Top 20)\n")
    for skill, count in stats["top_skills"]:
        lines.append(f"- {skill}: {count}\n")

    # 7. Average Quality Score
    lines.append("## 7. Average Quality Score\n")
    lines.append(f"- **Avg Quality Score**: {stats['avg_quality']}\n")

    # 8. City Coverage
    lines.append("## 8. City Coverage (Top 10)\n")
    for city, count in stats["by_city"].most_common(10):
        lines.append(f"- {city}: {count}\n")

    # 9. Company Coverage
    lines.append("## 9. Company Coverage (Top 10)\n")
    for company, count in stats["by_company"].most_common(10):
        lines.append(f"- {company}: {count}\n")

    # 10. Recommendations
    lines.append("## 10. Recommendations\n")
    if stats["empty_skills"] > 0:
        lines.append("- [WARN] Found empty skills. Run `python scripts/build_job_corpus.py --target-size 500` to fix.\n")
    if stats["empty_jd"] > 0:
        lines.append("- [WARN] Found empty JD. Check data sources for missing descriptions.\n")
    if stats["duplicate_title_ratio"] > 0.1:
        lines.append("- [WARN] High duplicate title ratio. Consider deduplication.\n")
    if stats["duplicate_tc_ratio"] > 0.05:
        lines.append("- [WARN] Duplicate (title, company, city) ratio > 5%. Review data sources.\n")
    if stats["avg_quality"] < 70:
        lines.append("- [WARN] Low avg quality score. Review data sources.\n")

    lines.append("\n---\n")
    lines.append("*Report generated by `scripts/analyze_job_corpus.py`*\n")

    return "".join(lines)


def main() -> None:
    print("[INFO] Loading job corpus...")
    jobs = load_jobs()
    if not jobs:
        return

    print(f"[INFO] Loaded {len(jobs)} jobs. Analyzing...")
    stats = analyze(jobs)

    print("[INFO] Generating report...")
    report = generate_report(stats)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")

    print(f"[OK] Report saved to {OUTPUT_PATH}")
    print(f"[SUMMARY] Total: {stats['total_jobs']}, Empty Skills: {stats['empty_skills']}, Empty JD: {stats['empty_jd']}")


if __name__ == "__main__":
    main()
