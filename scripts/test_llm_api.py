"""
test_llm_api.py — 验证 DeepSeek API 连通性 + 简单问答测试
"""
import sys
sys.path.insert(0, "src")

from llm_client import LLMClient

client = LLMClient()
print(f"LLM available: {client.available}")
print(f"base_url: {client.base_url}")
print(f"model: {client.model}")

if not client.available:
    print("❌ API Key 未配置或 openai 包未安装")
    sys.exit(1)

# 测试 1：简单问答
print("\n--- 测试 1：简单问答 ---")
resp = client.query("请用一句话介绍 Python")
print(f"回复: {resp}")

# 测试 2：JSON 输出
print("\n--- 测试 2：JSON 输出 ---")
json_resp = client.chat_json(
    system_prompt="你是一个 JSON 生成器。只输出纯 JSON，不要 markdown。",
    user_prompt='请生成一个包含 "name" 和 "score" 的 JSON，name=Offer捕手，score=95'
)
print(f"JSON 回复: {json_resp}")
print(f"类型: {type(json_resp)}")

# 测试 3：chat 方法
print("\n--- 测试 3：chat 方法 ---")
text = client.chat(
    system_prompt="你是求职顾问",
    user_prompt="大模型应用算法工程师需要哪些技能？",
    max_tokens=200
)
print(f"回复: {text[:100]}..." if text and len(text) > 100 else f"回复: {text}")

print("\n✅ 所有测试完成")
