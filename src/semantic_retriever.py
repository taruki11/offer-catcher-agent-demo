"""
Read-only semantic retriever based on sentence-transformers + FAISS.

This module is intentionally independent from the main rule ranker:
- no LLM API calls
- no training or save_pretrained
- no writes to Hugging Face cache or model folders
- model loading is lazy and read-only
"""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Optional

import numpy as np


_MODEL = None
_MODEL_NAME: Optional[str] = None
_DEVICE: Optional[str] = None
_FAISS_INDEX = None
_JOBS_CORPUS: list[dict] | None = None
_INDEX_SOURCE: Optional[str] = None


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _get_model():
    global _MODEL, _MODEL_NAME, _DEVICE
    if _MODEL is not None:
        return _MODEL

    model_path = os.getenv("SEMANTIC_MODEL_PATH", "").strip()
    model_name = os.getenv("SEMANTIC_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2").strip()
    selected = model_path if model_path and os.path.isdir(model_path) else model_name
    _MODEL_NAME = selected
    _DEVICE = _get_device()

    try:
        from sentence_transformers import SentenceTransformer

        print(f"[SemanticRetriever] loading model={selected} device={_DEVICE}")
        _MODEL = SentenceTransformer(selected, device=_DEVICE)
        print("[SemanticRetriever] model loaded")
        return _MODEL
    except Exception as exc:
        warnings.warn(f"SemanticRetriever model load failed: {exc}")
        _MODEL = None
        return None


def _require_faiss():
    try:
        import faiss

        return faiss
    except Exception as exc:
        warnings.warn(f"SemanticRetriever FAISS unavailable: {exc}")
        return None


def _build_job_text(job: dict) -> str:
    parts: list[str] = []
    for key in ("title", "company", "city", "direction", "jd"):
        value = job.get(key)
        if value:
            parts.append(str(value))
    for key in ("skills", "project_signals"):
        values = job.get(key) or []
        if isinstance(values, list):
            parts.append(" ".join(str(v) for v in values if v))
    return " ".join(parts)


def _load_corpus(corpus_path: str) -> list[dict]:
    path = Path(corpus_path)
    try:
        corpus = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.warn(f"SemanticRetriever corpus load failed: {exc}")
        return []
    if not isinstance(corpus, list):
        warnings.warn("SemanticRetriever corpus must be a list")
        return []
    print(f"[SemanticRetriever] corpus loaded: {path} ({len(corpus)} jobs)")
    return [item for item in corpus if isinstance(item, dict)]


def _build_faiss_index(corpus: list[dict]):
    model = _get_model()
    faiss = _require_faiss()
    if model is None or faiss is None:
        return None, corpus

    job_texts = [_build_job_text(job) for job in corpus]
    if not job_texts:
        return None, corpus

    print(f"[SemanticRetriever] encoding {len(job_texts)} job texts")
    embeddings = model.encode(job_texts, show_progress_bar=False, convert_to_numpy=True)
    embeddings = np.asarray(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    print(f"[SemanticRetriever] FAISS index ready: dim={embeddings.shape[1]} n={index.ntotal}")
    return index, corpus


def _ensure_index(corpus_path: str):
    global _FAISS_INDEX, _JOBS_CORPUS, _INDEX_SOURCE
    source = str(Path(corpus_path).resolve())
    if _FAISS_INDEX is not None and _JOBS_CORPUS is not None and _INDEX_SOURCE == source:
        return _FAISS_INDEX, _JOBS_CORPUS

    corpus = _load_corpus(corpus_path)
    if not corpus:
        _FAISS_INDEX = None
        _JOBS_CORPUS = []
        _INDEX_SOURCE = source
        return None, []

    _FAISS_INDEX, _JOBS_CORPUS = _build_faiss_index(corpus)
    _INDEX_SOURCE = source
    return _FAISS_INDEX, _JOBS_CORPUS


def _passes_target_filter(job: dict, target_role: Optional[str]) -> bool:
    if not target_role:
        return True
    target = target_role.strip()
    haystack = " ".join(
        str(job.get(key, ""))
        for key in ("title", "direction", "jd")
    )
    return target in haystack


def _make_reason(job: dict, score: float) -> str:
    title = job.get("title", "")
    direction = job.get("direction", "")
    skills = job.get("skills") or []
    if score >= 0.70:
        level = "high"
    elif score >= 0.50:
        level = "medium"
    else:
        level = "low"
    skill_text = ", ".join(str(v) for v in skills[:3])
    if skill_text:
        return f"{level} semantic match: {title} / {direction}; skills={skill_text}"
    return f"{level} semantic match: {title} / {direction}"


def query(
    resume_text: str,
    target_role: Optional[str] = None,
    corpus_path: Optional[str] = None,
    top_k: int = 5,
) -> list[dict]:
    if corpus_path is None:
        corpus_path = str(_project_root() / "data" / "jobs_corpus.json")

    index, corpus = _ensure_index(corpus_path)
    if index is None or not corpus:
        print("[SemanticRetriever] index unavailable; returning empty results")
        return []

    model = _get_model()
    faiss = _require_faiss()
    if model is None or faiss is None:
        return []

    resume_embedding = model.encode([resume_text], show_progress_bar=False, convert_to_numpy=True)
    resume_embedding = np.asarray(resume_embedding, dtype=np.float32)
    faiss.normalize_L2(resume_embedding)

    candidate_k = min(max(top_k * 5, top_k), len(corpus))
    distances, indices = index.search(resume_embedding, candidate_k)

    unfiltered: list[dict] = []
    filtered: list[dict] = []
    for score, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(corpus):
            continue
        source_job = corpus[idx]
        item = dict(source_job)
        item["semantic_score"] = round(float(score), 4)
        item["matched_reason"] = _make_reason(source_job, float(score))
        unfiltered.append(item)
        if _passes_target_filter(source_job, target_role):
            filtered.append(item)

    results = filtered[:top_k] if filtered else unfiltered[:top_k]
    print(f"[SemanticRetriever] returned {len(results)} jobs (top_k={top_k})")
    return results


def is_available() -> bool:
    return _get_model() is not None and _require_faiss() is not None
