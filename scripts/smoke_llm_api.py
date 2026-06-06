"""
scripts/smoke_llm_api.py — LLM API 冒烟测试
无 API Key 时输出 [SKIP]，有 API Key 时测试真实调用。
"""
import sys, pathlib, json, os
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

def main():
    from src.llm_client import LLMClient

    api_key = os.getenv("LLM_API_KEY", "")
    if not api_key:
        print("[SKIP] no API key configured (LLM_PROVIDER={}, MODEL={})".format(
            os.getenv("LLM_PROVIDER", "deepseek"),
            os.getenv("LLM_MODEL", "deepseek-chat")))
        print("[SKIP] set LLM_API_KEY in .env to run real API tests")
        return

    client = LLMClient()
    if not client.available:
        print("[SKIP] LLM client not available despite API key set")
        return

    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    print(f"[INFO] Provider={provider}, Model={model}, BaseURL={client.base_url}")

    # Test 1: chat_json with minimal JSON
    print("=== Test 1: chat_json (minimal JSON) ===")
    result = client.chat_json(
        "You are a JSON-only assistant. Output only valid JSON, no other text.",
        'Output: {"status": "ok", "value": 42}'
    )
    if result and result.get("status") == "ok":
        print(f"  [OK] chat_json returned valid response: {result}")
    else:
        print(f"  [FAIL] chat_json failed or returned unexpected: {result}")

    # Test 2: parse_resume_with_llm
    print("=== Test 2: parse_resume_with_llm ===")
    resume = "张同学 | 计算机硕士 | Python PyTorch Transformer RAG Agent"
    from src.resume_parser import parse_resume_with_llm
    profile = parse_resume_with_llm(resume, client)
    if profile and profile.get("skills"):
        print(f"  [OK] skills={profile['skills'][:5]}, has_llm={profile.get('has_llm_project')}, has_rec={profile.get('has_rec_project')}")
    else:
        print(f"  [FAIL] parse_resume_with_llm returned empty: {profile}")

    # Test 3: parse_jd_with_llm
    print("=== Test 3: parse_jd_with_llm ===")
    jd = "岗位：大模型应用算法实习生 | 公司：字节跳动 | 地点：北京 | 要求：Python PyTorch RAG Agent LangChain"
    from src.jd_parser import parse_jd_with_llm
    job = parse_jd_with_llm(jd, client)
    if job and job.get("title") and job.get("skills"):
        print(f"  [OK] title={job['title']}, skills={job['skills'][:5]}, direction={job.get('direction')}")
    else:
        print(f"  [FAIL] parse_jd_with_llm returned empty: {job}")

    # Test 4: Schema validation
    print("=== Test 4: Schema validation ===")
    profile_ok = bool(profile.get("skills") and isinstance(profile.get("skills"), list))
    job_ok = bool(job.get("title") and isinstance(job.get("skills"), list))
    if profile_ok and job_ok:
        print(f"  [OK] Both profile and job schema valid")
    else:
        print(f"  [FAIL] Schema validation failed: profile_ok={profile_ok}, job_ok={job_ok}")

    print("\n=== Smoke test completed ===")


if __name__ == "__main__":
    main()
