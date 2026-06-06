"""
import_public_jobs.py — 公开岗位导入脚本

支持：
  --from-fixture: 使用 test_data_ingestion.py 的 fixture 数据
  --limit N: 最多导入 N 条（默认 300）
  --output FILE: 输出文件路径（默认 data/public_jobs_sample.json）
  --update-merged: 是否更新 jobs_merged.json（默认 False，需显式指定）

用法：
  python scripts/import_public_jobs.py --from-fixture --limit 100
  python scripts/import_public_jobs.py --from-fixture --limit 300 --output data/public_jobs_big.json
  python scripts/import_public_jobs.py --from-fixture --limit 100 --update-merged  # 显式覆盖 jobs_merged.json
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.public_job_ingestion import (
    normalize_public_job,
    deduplicate_jobs,
    merge_jobs,
)

# Fixture 数据（从 test_data_ingestion 共享）
try:
    from scripts.test_data_ingestion import FIXTURE_JOBS
except ImportError:
    FIXTURE_JOBS = []


def import_from_fixture(limit: int, output_path: str, update_merged: bool = False):
    """从 fixture 数据导入岗位。"""
    if not FIXTURE_JOBS:
        print("[FAIL] No fixture data available. Run test_data_ingestion.py first.")
        return

    normalized = []
    for raw in FIXTURE_JOBS[:limit]:
        job = normalize_public_job(raw)
        if job:
            normalized.append(job)

    deduped = deduplicate_jobs(normalized)
    total = min(len(deduped), limit)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(deduped[:total], f, ensure_ascii=False, indent=2)

    print(f"[OK] Imported {total} jobs from fixture -> {output_path}")

    # 只有显式传入 --update-merged 时才更新 jobs_merged.json
    if update_merged:
        data_dir = os.path.dirname(output_path) or "data"
        merged_path = os.path.join(data_dir, "jobs_merged.json")
        builtin_path = os.path.join(data_dir, "jobs.json")

        if os.path.exists(builtin_path):
            with open(builtin_path, "r", encoding="utf-8") as f:
                builtin = json.load(f)
        else:
            builtin = []

        merged = merge_jobs(builtin, deduped[:total])
        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"[OK] jobs_merged.json: {len(merged)} jobs (builtin {len(builtin)} + public {total})")
    else:
        print("[INFO] --update-merged not set, skipping jobs_merged.json update")


def import_from_file(input_path: str, limit: int, output_path: str, update_merged: bool = False):
    """从 JSON/JSONL 文件导入岗位。"""
    if not os.path.exists(input_path):
        print(f"[FAIL] Input file not found: {input_path}")
        return

    raw_jobs = []
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        raw_jobs = data[:limit]
    elif isinstance(data, dict):
        raw_jobs = [data]
    else:
        print("[FAIL] Unsupported JSON format. Expected list or dict.")
        return

    normalized = []
    for raw in raw_jobs:
        job = normalize_public_job(raw)
        if job:
            normalized.append(job)

    deduped = deduplicate_jobs(normalized)
    total = min(len(deduped), limit)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(deduped[:total], f, ensure_ascii=False, indent=2)

    print(f"[OK] Imported {total} jobs from {input_path} -> {output_path}")

    # 只有显式传入 --update-merged 时才更新 jobs_merged.json
    if update_merged:
        data_dir = os.path.dirname(output_path) or "data"
        merged_path = os.path.join(data_dir, "jobs_merged.json")
        builtin_path = os.path.join(data_dir, "jobs.json")

        if os.path.exists(builtin_path):
            with open(builtin_path, "r", encoding="utf-8") as f:
                builtin = json.load(f)
        else:
            builtin = []

        merged = merge_jobs(builtin, deduped[:total])
        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"[OK] jobs_merged.json: {len(merged)} jobs (builtin {len(builtin)} + public {total})")
    else:
        print("[INFO] --update-merged not set, skipping jobs_merged.json update")


def main():
    parser = argparse.ArgumentParser(description="Import public jobs")
    parser.add_argument("--from-fixture", action="store_true", help="Use fixture data")
    parser.add_argument("--input", type=str, help="Input JSON/JSONL file path")
    parser.add_argument("--limit", type=int, default=300, help="Max jobs to import (default: 300)")
    parser.add_argument("--output", type=str, default="data/public_jobs_sample.json",
                        help="Output file path")
    parser.add_argument("--update-merged", action="store_true",
                        help="Update jobs_merged.json (default: False, must be explicit)")
    args = parser.parse_args()

    print("=" * 60)
    print("  import_public_jobs.py")
    print("=" * 60)
    print(f"[INFO] update_merged = {args.update_merged}")

    if args.from_fixture:
        import_from_fixture(args.limit, args.output, args.update_merged)
    elif args.input:
        import_from_file(args.input, args.limit, args.output, args.update_merged)
    else:
        print("[INFO] No input specified. Use --from-fixture or --input FILE.")
        print("[INFO] Defaulting to --from-fixture with limit=100...")
        import_from_fixture(100, args.output, args.update_merged)

    print("[OK] Done.")


if __name__ == "__main__":
    main()
