"""
test_online_workflow.py — 用真实 LLM API 跑完 9 个 Agent
"""
import sys, os, time

# 把项目根目录和 src/ 都加入 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from langgraph_workflow import run_online_demo

SAMPLE_RESUME = """
张三 | 大模型应用算法工程师
电话：13800000000 | 邮箱：zhangsan@email.com

教育背景
2022.09 - 2026.06  XX大学  计算机科学与技术  本科

实习经历
2025.06 - 2025.12  YY科技  算法实习生
- 参与大模型微调项目，使用 LoRA 对 Qwen2.5-7B 进行 SFT
- 使用 RAG 技术构建企业知识库问答系统（FAISS + Sentence Transformers）
- 开发 Semantic Scholar 论文检索工具，支持 200+ 并发查询

项目经历
2024.09 - 2025.06  Offer捕手 — 智能求职匹配系统
- 构建基于 Sentence Transformers 的语义匹配引擎，NDCG@10=0.87
- 设计多 Agent 决策流水线（9个 Agent 协作）
- 部署 HuggingFace Space 公网 Demo

技能
Python, PyTorch, Transformers, LangChain, FAISS, Sentence Transformers
"""

print("=" * 60)
print("🚀 开始在线模式测试（真实 LLM API）")
print("=" * 60)

t0 = time.time()
try:
    state = run_online_demo(SAMPLE_RESUME, goal="找大模型应用算法相关实习")
except Exception as e:
    print(f"❌ 工作流执行失败: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

elapsed = time.time() - t0
print(f"\n✅ 工作流执行完毕，耗时 {elapsed:.1f}s")
print("=" * 60)

# 打印每个 Agent 的输出摘要
print("\n📋 Agent 执行结果：\n")

# 1. CareerIntent
intent = state.intent
print(f"1️⃣ CareerIntent  →  方向:{intent.direction}  阶段:{intent.stage}  城市:{intent.target_cities}  风险:{intent.risk_preference}")
if intent.reasoning:
    print(f"   理由: {intent.reasoning[:80]}")

# 2. JobScout
print(f"\n2️⃣ JobScout  →  找到 {len(state.jds)} 个岗位")
for i, jd in enumerate(state.jds[:3]):
    print(f"   [{i+1}] {jd.title} @ {jd.company}  {jd.city}")

# 3. JDAnalyst
print(f"\n3️⃣ JDAnalyst  →  分析了 {len(state.jds)} 个 JD")
if state.jds and state.jds[0].hard_skills:
    print(f"   样例技能: {state.jds[0].hard_skills[:5]}")

# 4. ResumeEvidence
ev = state.resume_evidence
print(f"\n4️⃣ ResumeEvidence  →  技能证据:{len(ev.skill_evidence)}  缺口:{len(ev.gap_areas)}")
for sk in list(ev.skill_evidence.keys())[:3]:
    evidence_list = ev.skill_evidence[sk]
    evidence_str = evidence_list[0] if evidence_list else ""
    print(f"   ✅ {sk} (证据: {evidence_str[:50]}...)")
for gap in ev.gap_areas[:2]:
    print(f"   ⚠️ 缺口: {gap}")

# 5. MatchReasoning
print(f"\n5️⃣ MatchReasoning  →  匹配了 {len(state.match_results)} 个岗位")
for r in state.match_results[:3]:
    print(f"   [{r.title}] {r.company}  分数:{r.match_score:.1f}  动作:{r.apply_action}")
    if r.evidence_based_reasoning:
        print(f"   理由: {r.evidence_based_reasoning[:80]}...")

# 6. CounterfactualPlanning
cf = state.counterfactual
print(f"\n6️⃣ CounterfactualPlanning  →  {len(cf.top3_payoffs)} 个补强建议")
for p in cf.top3_payoffs:
    print(f"   补强: {p.get('action','?')}  分数提升:+{p.get('match_gain','?')}  天数:{p.get('effort_days','?')}  原因:{p.get('why','')}")

# 7. ResumeCoach
coach = state.coach
print(f"\n7️⃣ ResumeCoach  →  可改写:{len(coach.can_rewrite)}  需先补:{len(coach.need_project_first)}  勿造假:{len(coach.dont_fabricate)}")
for item in coach.can_rewrite[:2]:
    print(f"   ✏️ 可改写: {item}")
for item in coach.need_project_first[:2]:
    print(f"   🔧 需先补: {item}")

# 8. InterviewCoach
interview = state.interview_prep
print(f"\n8️⃣ InterviewCoach  →  {len(interview.likely_questions)} 个问题  {len(interview.prep_plan_7day)}天计划")
for q in interview.likely_questions[:3]:
    print(f"   Q: {q}")
print(f"   复习重点: {interview.focus_areas[:3]}")

# 9. StrategyPlanner
strategy = state.strategy
print(f"\n9️⃣ StrategyPlanner  →  稳投:{len(strategy.safe_jobs)}  冲刺:{len(strategy.stretch_jobs)}  跳过:{len(strategy.skip_jobs)}")
for s in strategy.safe_jobs[:2]:
    print(f"   ✅ 稳投: {s.title} @ {s.company}")
for s in strategy.stretch_jobs[:2]:
    print(f"   🚀 冲刺: {s.title} @ {s.company}")

print("\n" + "=" * 60)
print("🎉 全部 9 个 Agent 执行成功！")
print("=" * 60)

# 打印 Agent trace
print("\n📋 Agent Trace：")
for line in state.agent_trace:
    print(f"  {line}")
