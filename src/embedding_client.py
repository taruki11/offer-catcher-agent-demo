"""
embedding_client.py — 语义向量召回客户端
支持两种模式：
1. API 模式（DeepSeek / OpenAI / Qwen 兼容嵌入接口）
2. 本地 sentence-transformers 模式（可选，需安装）

优先级：API → sentence-transformers → token cosine fallback
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # python-dotenv is optional; env vars still work.
    def load_dotenv(*args, **kwargs):
        return False


load_dotenv()


class EmbeddingClient:
    """统一嵌入接口。未配置时自动回退。"""

    def __init__(self) -> None:
        self.api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("EMBEDDING_BASE_URL") or os.getenv("LLM_BASE_URL")
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-v1")
        self.provider = os.getenv("EMBEDDING_PROVIDER", "").lower()
        self._client = None
        self._local_model = None
        self.mode: Optional[str] = None  # "api" | "local" | None

        # 尝试加载 API 模式
        if self.api_key and self.base_url:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                self.mode = "api"
                print(f"[OK] EmbeddingClient: API 模式 ({self.base_url})")
            except Exception as exc:
                print(f"[WARN] EmbeddingClient API 初始化失败：{exc}")

        # API 失败则尝试本地模型  
        if self.mode is None:
            self._try_load_local()

    def _try_load_local(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
            self._local_model = SentenceTransformer(model_name)
            self.mode = "local"
            print(f"[OK] EmbeddingClient: 本地模式 ({model_name})")
        except Exception:
            self.mode = None

    def is_available(self) -> bool:
        return self.mode is not None

    def embed(self, texts: list[str]) -> Optional[list[list[float]]]:
        """批量获取嵌入向量。返回 List[List[float]] 或 None。"""
        if self.mode == "api":
            return self._embed_api(texts)
        if self.mode == "local":
            return self._embed_local(texts)
        return None

    def _embed_api(self, texts: list[str]) -> Optional[list[list[float]]]:
        try:
            resp = self._client.embeddings.create(model=self.model, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as exc:
            print(f"[WARN] Embedding API 调用失败：{exc}")
            return None

    def _embed_local(self, texts: list[str]) -> Optional[list[list[float]]]:
        try:
            embeddings = self._local_model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as exc:
            print(f"[WARN] 本地嵌入失败：{exc}")
            return None

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """余弦相似度。"""
        if not vec1 or not vec2:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def semantic_similarity(self, resume_text: str, job_text: str) -> Optional[float]:
        """计算简历与岗位的语义相似度（0~1）。"""
        embeddings = self.embed([resume_text, job_text])
        if embeddings is None:
            return None
        return self.cosine_similarity(embeddings[0], embeddings[1])

    def rank_by_semantic(
        self, resume_text: str, jobs: list[dict], top_k: int = 8
    ) -> list[tuple[int, float]]:
        """用语义向量对岗位重新排序。返回 [(index, score), ...] 按分数降序。"""
        if not self.is_available():
            return []
        texts = [f"{j.get('title', '')} {j.get('jd', '')}" for j in jobs]
        all_texts = [resume_text] + texts
        embeddings = self.embed(all_texts)
        if embeddings is None:
            return []
        resume_emb = embeddings[0]
        scores: list[tuple[int, float]] = []
        for i, job_emb in enumerate(embeddings[1:], start=0):
            sim = self.cosine_similarity(resume_emb, job_emb)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def get_embedding_client() -> EmbeddingClient:
    """工厂函数。"""
    return EmbeddingClient()
