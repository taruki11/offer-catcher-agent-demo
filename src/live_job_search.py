"""
live_job_search.py — 联网岗位搜索（Stub）
当前为预留接口，返回空列表。

未来可接入：
- Bing Search API / SerpAPI / Tavily Search
- 自有招聘网站爬虫（需遵守 ToS）
- 学校就业平台上发布的岗位信息

注意：不要强行爬需要登录的网站，不要违反招聘网站 ToS。
"""

from __future__ import annotations


def search_jobs(query: str, city: str = "", stage: str = "", limit: int = 10) -> list[dict]:
    """
    联网搜索岗位，返回与 jobs.json 兼容的 dict 列表。
    当前为 Stub，需配置搜索 API 后才能使用。
    """
    # TODO: 接入真实搜索 API
    # import requests
    # response = requests.get("https://api.serpapi.com/search", params={...})
    # return _parse_search_results(response.json())
    return []


def is_available() -> bool:
    """检查联网搜索是否可用。"""
    return False
