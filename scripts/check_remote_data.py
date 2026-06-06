import json
import sys
from pathlib import Path

corpus_path = Path("data/jobs_corpus.json")
merged_path = Path("data/jobs_merged.json")

ok = True

if corpus_path.exists():
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    print(f"jobs_corpus {len(corpus)}")
    ok = ok and len(corpus) >= 500
else:
    print("jobs_corpus NOT FOUND")
    ok = False

if merged_path.exists():
    merged = json.loads(merged_path.read_text(encoding="utf-8"))
    print(f"jobs_merged {len(merged)}")
    ok = ok and len(merged) >= 500
else:
    print("jobs_merged NOT FOUND")
    ok = False

if not ok:
    print("REMOTE_DATA_CHECK_FAIL: jobs_corpus/jobs_merged must both exist and contain >=500 jobs", file=sys.stderr)
    raise SystemExit(1)

print("REMOTE_DATA_CHECK_OK")
