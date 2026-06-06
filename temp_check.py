import json
from pathlib import Path

try:
    corpus = json.loads(Path("data/jobs_corpus.json").read_text(encoding="utf-8"))
    merged = json.loads(Path("data/jobs_merged.json").read_text(encoding="utf-8"))
    print(f"jobs_corpus.json: {len(corpus)} 条")
    print(f"jobs_merged.json: {len(merged)} 条")
except Exception as e:
    print(f"错误: {e}")
