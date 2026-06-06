"""
llm_client.py — LLM API 适配层（多 Provider 支持）
支持：DeepSeek / OpenAI / 通义千问 / 混元（均支持 OpenAI-compatible 接口）

配置方式：.env 文件或环境变量
  LLM_API_KEY=xxx          # 必填
  LLM_BASE_URL=xxx         # API 端点（默认 OpenAI）
  LLM_MODEL=gpt-4o-mini    # 模型名
  LLM_PROVIDER=openai      # openai / deepseek / qwen / hunyuan
"""
import json, os, re, hashlib
from pathlib import Path
from typing import Optional

_RESPONSE_CACHE: dict[str, str] = {}  # 新增：响应缓存字典

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # python-dotenv is optional for deployed demos.
    def load_dotenv(*args, **kwargs):
        return False

# Provider 默认 Base URL
PROVIDER_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "hunyuan": "https://api.hunyuan.cloud.tencent.com/v1",
}


class LLMClient:
    """LLM API 适配器。未配置 API Key 时 available=False，所有方法 fallback。"""

    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.available = bool(self.api_key)
        self._client = None

        # 自动探测 base_url
        if not self.base_url:
            self.base_url = PROVIDER_URLS.get(provider, PROVIDER_URLS["openai"])

        if self.available:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception:
                self.available = False

    def chat(self, system_prompt: str, user_prompt: str = None, temperature: float = 0.25, max_tokens: int = 800) -> Optional[str]:
        """通用 LLM 调用，返回文本或 None（失败时）。"""
        if not self.available or self._client is None:
            return None
        # 参数处理
        if user_prompt is None:
            user_prompt = system_prompt
            system_prompt = "你是 Offer 捕手 AI 求职顾问。请用 JSON 格式回复。"
        # 缓存检查
        cache_key = hashlib.sha256(f"{system_prompt}|{user_prompt}|{temperature}|{max_tokens}".encode()).hexdigest()
        if cache_key in _RESPONSE_CACHE:
            return _RESPONSE_CACHE[cache_key]
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content
            _RESPONSE_CACHE[cache_key] = text
            return text
        except Exception:
            return None

    def chat_json(self, system_prompt: str, user_prompt: str) -> Optional[dict]:
        """LLM 调用并强制 JSON 输出。返回 dict 或 None。"""
        text = self.chat(system_prompt, user_prompt, temperature=0.1)
        if text is None:
            return None
        return _extract_json(text)

    def enhance_matches(self, profile: dict, ranked_jobs: list[dict]) -> list[dict]:
        if not self.available or self._client is None:
            return ranked_jobs

    def query(self, prompt: str, temperature: float = 0.3, max_tokens: int = 800) -> Optional[str]:
        """便捷调用：单 prompt → 文本回复。"""
        return self.chat(
            system_prompt="你是 Offer 捕手 AI 求职顾问。请用 JSON 格式回复，不要 markdown codeblock。",
            user_prompt=prompt,
            temperature=temperature,
                max_tokens=max_tokens,
        )

    def enhance_matches_impl(self, profile: dict, ranked_jobs: list[dict]) -> list[dict]:
        prompt_template = (
            Path(__file__).resolve().parents[1] / "prompts" / "match_analysis.md"
        ).read_text(encoding="utf-8")
        enhanced = []
        for job in ranked_jobs:
            prompt = prompt_template.format(
                profile=json.dumps(profile, ensure_ascii=False),
                job=json.dumps(job, ensure_ascii=False),
            )
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是专业的大模型应用算法求职匹配 Agent。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.25,
                )
                job = dict(job)
                job["llm_analysis"] = response.choices[0].message.content
            except Exception as exc:
                job = dict(job)
                job["llm_analysis"] = f"LLM 调用失败，已保留规则版诊断：{exc}"
            enhanced.append(job)
        return enhanced


def _extract_json(text: str) -> Optional[dict]:
    """从 LLM 输出中提取 JSON（容忍 markdown code block 包裹）。"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 尝试 ```json ... ``` 包裹
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 尝试找到第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None
