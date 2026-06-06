"""
job_intake.py — JD Intake 管道
- 解析单个 / 多个 JD 文本
- 标准化后与 jobs.json 格式兼容
- 去重、合并内置与用户岗位
"""
from __future__ import annotations

import json
from pathlib import Path

from src.jd_parser import parse_jd, parse_jd_with_llm


def parse_single_jd(text: str, llm_client=None) -> dict:
    """解析单条 JD 文本；传入 llm_client 时优先走 LLM，失败自动 fallback。"""
    if llm_client is not None:
        return parse_jd_with_llm(text, llm_client)
    return parse_jd(text)


def parse_multiple_jds(text: str, separator: str = "---JD---", llm_client=None) -> list[dict]:
    """按分隔符切分多条 JD，分别解析。也支持空行分隔（至少 2 个连续换行）。"""
    # 先尝试显式分隔符
    if separator in text:
        chunks = [c.strip() for c in text.split(separator) if c.strip()]
    else:
        # 回退：按空行切分（连续 2+ 换行）
        import re
        chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if len(c.strip()) > 20]

    results = []
    for chunk in chunks:
        try:
            job = parse_single_jd(chunk, llm_client=llm_client)
            results.append(job)
        except Exception:
            # 跳过一次失败的解析
            pass
    return results


def normalize_job(job: dict) -> dict:
    """确保单个 job dict 有所有必需字段，缺失补默认值。"""
    defaults = {
        "id": "unknown",
        "title": "未知岗位",
        "company": "未知公司",
        "city": "不限",
        "direction": "通用",
        "stage": "不限",
        "skills": [],
        "project_signals": [],
        "jd": "",
        "hard_requirements": [],
        "bonus_requirements": [],
        "risk_flags": [],
        "interview_themes": ["算法基础"],
        "source": "builtin",
        "raw_text": "",
    }
    for key, val in defaults.items():
        job.setdefault(key, val)
    return job


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """按 title 去重，保留第一个。"""
    seen = set()
    result = []
    for job in jobs:
        title = job.get("title", "").strip().lower()
        if title and title not in seen:
            seen.add(title)
            result.append(job)
    return result


def merge_builtin_and_user_jobs(
    builtin_jobs: list[dict], user_jobs: list[dict]
) -> list[dict]:
    """合并内置岗位库 + 用户粘贴岗位。用户岗位优先（同 title 覆盖内置）。"""
    # 标准化所有岗位
    builtin = [normalize_job(j) for j in builtin_jobs]
    user = [normalize_job(j) for j in user_jobs]
    # 用户覆盖内置
    user_titles = {j.get("title", "").strip().lower() for j in user}
    merged = [j for j in builtin if j.get("title", "").strip().lower() not in user_titles]
    merged.extend(user)
    return merged


def load_builtin_jobs(path: str | Path) -> list[dict]:
    """加载内置 jobs.json。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
