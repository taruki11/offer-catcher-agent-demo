"""
Job Scout Agent — 主动找岗位，不是 RAG 检索。

数据源优先级：
1. 联网搜索 API（需要配置 SEARCH_API_KEY）
2. 用户粘贴的 JD
3. 本地岗位缓存（jobs_corpus.json）
"""

from agent_state import JDProfile, CareerIntent


class JobScoutAgent:
    def __init__(self, llm_client=None, search_client=None):
        self.llm = llm_client
        self.search = search_client

    def scout(self, intent: CareerIntent, user_jds: list[dict] | None = None,
              local_corpus: list[dict] | None = None) -> list[JDProfile]:
        """搜索岗位，返回 JDProfile 列表。"""
        results: list[JDProfile] = []

        # 1. 用户粘贴的 JD
        if user_jds:
            for jd in user_jds:
                results.append(JDProfile(
                    title=jd.get("title", ""),
                    company=jd.get("company", ""),
                    city=jd.get("city", "不限"),
                    salary=jd.get("salary", ""),
                    jd_text=jd.get("jd_text", jd.get("description", "")),
                    source_url="用户粘贴",
                ))

        # 2. 本地岗位缓存
        if local_corpus:
            for job in local_corpus:
                jd_title = job.get("title", "")
                jd_company = job.get("company", "")
                jd_dir = job.get("direction", "")
                # 方向过滤
                if intent.direction != "待确认" and jd_dir:
                    if self._direction_match(intent.direction, jd_dir):
                        results.append(self._from_corpus(job))
                else:
                    results.append(self._from_corpus(job))

        # 3. 联网搜索（如果配置了 API）
        if self.search and len(results) < 10:
            try:
                web_jds = self.search(intent.direction, intent.target_cities, intent.stage)
                results.extend(web_jds)
            except Exception:
                pass

        # 按城市过滤排序
        results.sort(key=lambda x: (
            0 if x.city in intent.target_cities else 1,
            -(len(x.hard_skills))
        ))

        # 如果过滤后没有结果，不做方向过滤（回退）
        if not results and local_corpus:
            for job in local_corpus:
                results.append(self._from_corpus(job))

        # 二次过滤：去掉明显非中国公司的岗位
        foreign_companies = {'Capgemini','Home Depot','The Home Depot','Lockheed Martin','EverCommerce','LinkedIn',
                             'Leidos','Meta','Google','Amazon','Apple','Microsoft','OpenAI','Canva','Talkspace',
                             'Netflix','Salesforce','Command Post Technologies'}
        results = [r for r in results if r.company not in foreign_companies]

        return results[:20]  # 最多返回 20 个

    def _direction_match(self, intent_dir: str, jd_dir: str) -> bool:
        """方向匹配：Agent/LLM/大模型/NLP/深度学习/CV 视为同一大类。"""
        i = intent_dir.lower()
        j = jd_dir.lower()
        if i == j: return True
        ai_kw = ["大模型", "agent", "llm", "nlp", "应用", "深度学习", "计算机视觉", "算法"]
        if any(k in i for k in ai_kw) and any(k in j for k in ai_kw): return True
        if "推荐" in i and "推荐" in j: return True
        if "搜索" in i and "搜索" in j: return True
        return False

    def _from_corpus(self, job: dict) -> JDProfile:
        return JDProfile(
            title=job.get("title", ""),
            company=job.get("company", ""),
            city=job.get("city", "不限"),
            salary=job.get("salary", ""),
            source_url=job.get("url", job.get("source_url", "")),
            jd_text=job.get("jd_text", job.get("description", "")),
            hard_skills=job.get("skills", []) if isinstance(job.get("skills"), list) else [],
            direction=job.get("direction", ""),
            stage=job.get("stage", job.get("recruit_type", "")),
        )
