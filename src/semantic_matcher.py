"""
语义匹配模块 - 使用 Sentence Transformers 进行真实语义理解
替代原来的字符级 cosine_similarity
"""

import os
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer, util


class SemanticMatcher:
    """
    使用 Sentence Transformers 进行简历-JD 语义匹配
    支持中文和英文混合场景
    """

    def __init__(self, model_name: str = None):
        """
        初始化语义匹配器
        
        Args:
            model_name: 模型名称或本地路径
                - 如果为 None，从环境变量 SEMANTIC_MODEL_PATH 读取
                - 如果环境变量也未设置，使用 "BAAI/bge-large-zh-v1.5"
                - 如果路径存在，从本地加载；否则从 HuggingFace 下载
        """
        if model_name is None:
            model_name = os.getenv("SEMANTIC_MODEL_PATH", "BAAI/bge-large-zh-v1.5")
        
        # 检查是否为本地路径
        if os.path.isdir(model_name):
            print(f"📥 从本地加载语义匹配模型: {model_name}")
        else:
            print(f"📥 加载语义匹配模型: {model_name} (若无缓存将自动下载)")
        
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        将文本列表编码为向量
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            numpy array, shape: (len(texts), embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings

    def compute_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        计算简历和 JD 的语义相似度
        
        Args:
            resume_text: 简历全文
            jd_text: JD 全文或拼接文本
            
        Returns:
            float: 相似度分数 (0-1)
        """
        # 编码
        resume_embedding = self.model.encode(resume_text)
        jd_embedding = self.model.encode(jd_text)

        # 计算余弦相似度
        similarity = util.cos_sim(resume_embedding, jd_embedding).item()
        return float(similarity)

    def batch_match(self, resume_text: str, jobs: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        批量匹配简历和多个岗位
        
        Args:
            resume_text: 简历全文
            jobs: 岗位列表
            top_k: 返回 TopK
            
        Returns:
            带 semantic_score 的岗位列表（按分数降序）
        """
        # 构建 JD 文本列表
        jd_texts = []
        for job in jobs:
            jd_text = f"{job['title']} {job.get('jd', '')} {' '.join(job.get('skills', []))}"
            jd_texts.append(jd_text)

        # 批量编码
        resume_embedding = self.model.encode(resume_text)
        jd_embeddings = self.model.encode(jd_texts)

        # 计算相似度
        similarities = util.cos_sim(resume_embedding, jd_embeddings)[0]

        # 附加分数并排序
        scored_jobs = []
        for i, job in enumerate(jobs):
            job_copy = job.copy()
            job_copy["semantic_score"] = float(similarities[i])
            scored_jobs.append(job_copy)

        scored_jobs.sort(key=lambda x: x["semantic_score"], reverse=True)
        return scored_jobs[:top_k]

    def skill_matching(self, resume_text: str, required_skills: List[str]) -> Dict[str, float]:
        """
        计算简历对每个技能的匹配度
        
        Args:
            resume_text: 简历全文
            required_skills: 岗位要求的技能列表
            
        Returns:
            Dict[skill] = match_score (0-1)
        """
        # 编码
        skill_embeddings = self.model.encode(required_skills)
        resume_embedding = self.model.encode(resume_text)

        # 计算每个技能和简历的相似度
        similarities = util.cos_sim(resume_embedding, skill_embeddings)[0]

        return {skill: float(score) for skill, score in zip(required_skills, similarities)}


# ---------------------------------------------------------------------------
# 使用示例（可以被 matcher.py 调用）
# ---------------------------------------------------------------------------

def enhance_matcher_with_semantic(resume_text: str, jobs: List[Dict], top_k: int = 10):
    """
    用语义匹配增强原来的规则匹配
    
    Returns:
        DataFrame with columns: [job_info..., semantic_score, hybrid_score]
    """
    matcher = SemanticMatcher()

    # 语义召回
    semantic_results = matcher.batch_match(resume_text, jobs, top_k=top_k * 2)

    # 和原来的规则分数融合
    for job in semantic_results:
        # 原来规则的 match_score (假设已经计算好)
        rule_score = job.get("match_score", 50)

        # 语义分数 (0-1) 转成 0-100
        semantic_score = job["semantic_score"] * 100

        # 混合分数：规则权重 0.4，语义权重 0.6
        job["hybrid_score"] = 0.4 * rule_score + 0.6 * semantic_score

    # 按混合分数重排序
    semantic_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return semantic_results[:top_k]


if __name__ == "__main__":
    # 测试代码
    sample_resume = """
    张同学，熟悉 Python、PyTorch、Transformer、RAG、Agent。
    项目经历：GenAdRec 生成式广告推荐、LLM 求职助手 Demo。
    """

    sample_jobs = [
        {"title": "大模型应用算法实习生", "jd": "负责 RAG、Agent、Embedding", "skills": ["LLM", "RAG", "Agent"]},
        {"title": "后端研发实习生", "jd": "负责 API 开发、SQL 优化", "skills": ["Python", "FastAPI", "SQL"]},
    ]

    matcher = SemanticMatcher()
    results = matcher.batch_match(sample_resume, sample_jobs, top_k=2)

    print("\n🎯 语义匹配结果：")
    for i, job in enumerate(results, 1):
        print(f"{i}. {job['title']} (语义分数: {job['semantic_score']:.3f})")
