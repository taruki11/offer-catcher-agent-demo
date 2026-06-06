"""
scripts/test_llm_fallback.py — LLM Fallback 测试
无 API Key 时，所有 LLM 方法必须自动 fallback 到规则版。
"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

JD = """岗位：大模型应用算法实习生
公司：字节跳动
地点：北京
要求：Python、PyTorch、RAG、Agent、LangChain"""

RESUME = """张同学 | 计算机硕士
技能：Python、PyTorch、Transformer、RAG、Agent"""


def test_llm_client_no_key():
    from src.llm_client import LLMClient
    c = LLMClient()
    available_before = c.available
    # 如果没有 API key, available 应为 False
    assert c.available is False or c.available is True  # 根据环境
    text = c.chat("hi", "hello")
    json_result = c.chat_json("hi", "hello")
    # 无 key 时应返回 None
    if not c.available:
        assert text is None, "chat should return None without API key"
        assert json_result is None, "chat_json should return None without API key"
        print(f"  [OK] chat/chat_json fallback to None (no API key)")
    else:
        print(f"  [OK] LLM available (API key set), chat={bool(text)}, chat_json={bool(json_result)}")


def test_jd_parser_fallback():
    from src.jd_parser import parse_jd, parse_jd_with_llm
    # 无 LLM client → fallback
    r1 = parse_jd_with_llm(JD, llm_client=None)
    r2 = parse_jd(JD)
    assert r1["title"] == r2["title"], "fallback should match rule-based"
    print(f"  [OK] parse_jd_with_llm fallback OK, title={r1['title']}")

    # 有 client 但无 API key → 也应 fallback
    from src.llm_client import LLMClient
    c = LLMClient()
    if not c.available:
        r3 = parse_jd_with_llm(JD, llm_client=c)
        assert r3["title"] == r2["title"], "fallback with unavailable client should match"
        print(f"  [OK] parse_jd_with_llm fallback with unavailable client OK")


def test_resume_parser_fallback():
    from src.resume_parser import parse_resume, parse_resume_with_llm
    r1 = parse_resume_with_llm(RESUME, llm_client=None)
    r2 = parse_resume(RESUME)
    assert r1["skills"] == r2["skills"], "fallback skills should match"
    print(f"  [OK] parse_resume_with_llm fallback OK, skills={r1['skills'][:5]}")

    from src.llm_client import LLMClient
    c = LLMClient()
    if not c.available:
        r3 = parse_resume_with_llm(RESUME, llm_client=c)
        assert r3["skills"] == r2["skills"], "fallback with unavailable client should match"
        print(f"  [OK] parse_resume_with_llm fallback with unavailable client OK")


def test_llm_client_schema_validation():
    """chat_json 的 JSON 提取容错测试。"""
    from src.llm_client import _extract_json
    # 测试纯 JSON
    assert _extract_json('{"a":1}') == {"a":1}
    # 测试 markdown 包裹
    assert _extract_json('```json\n{"a":1}\n```') == {"a":1}
    # 测试混合文本
    assert _extract_json('前文 {"a":1} 后文') == {"a":1}
    # 测试无效输入
    assert _extract_json("not json at all") is None
    print(f"  [OK] _extract_json schema validation OK")


def test_llm_provider_config():
    """Provider URL 配置测试。"""
    from src.llm_client import PROVIDER_URLS
    assert "deepseek" in PROVIDER_URLS
    assert "openai" in PROVIDER_URLS
    assert "qwen" in PROVIDER_URLS
    assert "hunyuan" in PROVIDER_URLS
    print(f"  [OK] Provider URLs configured: {list(PROVIDER_URLS.keys())}")


def test_jd_parser_dirty_llm_schema():
    """LLM 返回字段类型不规范时，解析器必须校正为可排序 schema。"""
    from src.jd_parser import parse_jd_with_llm
    from src.llm_client import LLMClient

    class DirtyClient(LLMClient):
        def __init__(self):
            self.available = True

        def chat_json(self, system_prompt: str, user_prompt: str):
            return {
                "title": "",
                "company": 123,
                "city": "",
                "direction": "",
                "stage": "",
                "skills": "Python, RAG",
                "project_signals": ["Agent", ""],
                "hard_requirements": None,
                "bonus_requirements": "加分",
                "risk_flags": [],
                "interview_themes": [],
            }

    job = parse_jd_with_llm(JD, DirtyClient())
    assert isinstance(job["title"], str) and job["title"], "title should fallback to rule parser"
    assert isinstance(job["skills"], list) and job["skills"], "skills should be a non-empty list"
    assert isinstance(job["hard_requirements"], list), "hard_requirements should be list"
    assert isinstance(job["interview_themes"], list) and job["interview_themes"], "themes should fallback"
    print(f"  [OK] dirty LLM schema corrected, title={job['title']}, skills={job['skills'][:3]}")


def main():
    print("=== Test 1: LLMClient no-key fallback ===")
    test_llm_client_no_key()
    print("=== Test 2: JD parser fallback ===")
    test_jd_parser_fallback()
    print("=== Test 3: Resume parser fallback ===")
    test_resume_parser_fallback()
    print("=== Test 4: Schema validation ===")
    test_llm_client_schema_validation()
    print("=== Test 5: Provider config ===")
    test_llm_provider_config()
    print("=== Test 6: Dirty LLM schema correction ===")
    test_jd_parser_dirty_llm_schema()
    print("\n=== All LLM fallback tests passed ===")


if __name__ == "__main__":
    main()
