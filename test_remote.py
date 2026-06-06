"""
test_remote.py — 3060 核心工作流测试
测试内容：parse_resume() → rank_jobs() → gen_strategy_package() → generate_report()
运行方式：python test_remote.py
"""

import sys, json, pathlib

# 确保能用项目模块
sys.path.insert(0, "D:/Pycharm_workplace/offer_catcher_agent_demo_20260602")

from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.conversion import attach_conversion_scores
from src.strategy_planner import gen_strategy_package
from src.report_generator import generate_report

SAMPLE = """张同学 | 计算机科学与技术 | 2026 届硕士

求职方向：大模型应用算法 / 推荐算法实习生，期望城市深圳或北京。

技能：Python、PyTorch、Transformer、RAG、Agent、Embedding、FAISS、LangChain、推荐系统、召回排序、NDCG、A/B Test、SQL。

项目经历：
1. GenAdRec 生成式广告推荐项目：基于 Transformer 建模用户行为序列，将广告候选集转化为生成式 likelihood rerank 问题；构建 Semantic ID 表示广告 item，结合多兴趣召回提升 NDCG@10。
2. LLM 求职助手 Demo：使用 DeepSeek API 和 bge embedding 实现 JD 检索、简历关键词诊断、Prompt 模板优化，支持输出岗位匹配解释。
3. MIND 多兴趣推荐复现：复现 capsule routing 用户多兴趣建模，在公开数据集上对比召回 HitRate 与 NDCG。

实习经历：
曾参与推荐系统离线评估脚本开发，负责样本构造、特征清洗和模型结果分析。

补充：希望找能结合 LLM、Agent、RAG 和推荐排序的算法岗位。"""


def main():
    print("=== Agent 1: Profile Builder ===")
    profile = parse_resume(SAMPLE)
    skills = profile.get("skills", [])
    print(f"命中技能数：{len(skills)}")
    print(f"前 5 项技能：{skills[:5]}")
    assert len(skills) > 0, "技能解析失败"
    print("[OK] Profile Builder")

    print("\n=== Agent 3/4: Opportunity Scout + Application Ranker ===")
    scored = rank_jobs(
        resume_text=SAMPLE,
        profile=profile,
        target_role="大模型应用算法",
        target_city="深圳",
        stage="实习",
        top_k=5,
        jobs_path=pathlib.Path("D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/data/jobs.json"),
    )
    print(f"召回岗位数：{len(scored)}")
    assert len(scored) > 0, "召回失败"
    top1 = scored[0]
    print(f"Top1: {top1.get('title', '')} | ApplyPriority={top1.get('apply_priority', '-')}")
    print(f"  匹配分={top1.get('match_score', '-')}  通过分={top1.get('pass_score', '-')}  风险分={top1.get('risk_score', '-')}")
    print("[OK] Scout + Ranker")

    print("\n=== Agent 5/6: Gap Diagnosis + Resume Conversion ===")
    conv_scored = attach_conversion_scores(scored, profile)
    gap_count = sum(len(j.get("gaps", [])) for j in conv_scored)
    rewrite_count = sum(len(j.get("rewrites", [])) for j in conv_scored)
    print(f"能力缺口数：{gap_count}")
    print(f"改写建议数：{rewrite_count}")
    print("[OK] Gap + Conversion")

    print("\n=== Agent 7: Strategy Planner ===")
    strategy = gen_strategy_package(conv_scored, profile)
    top3 = strategy.get("priority_top3", [])
    print(f"Top3 推荐数：{len(top3)}")
    if top3:
        print(f"  Top1: {top3[0].get('title', '')} | 动作={top3[0].get('apply_action', '')}")
    print("[OK] Strategy Planner")

    print("\n=== 报告生成 ===")
    md = generate_report(profile, conv_scored, strategy)
    print(f"报告长度：{len(md)} 字符")
    assert len(md) > 100, "报告生成异常"
    print("[OK] Report Generator")

    print("\n========== 全部测试通过 [OK] ==========")


if __name__ == "__main__":
    main()
