"""
Report Generator — Markdown 求职策略报告导出模块
一键生成包含岗位排序、简历优化建议、7 天投递策略、面试准备的完整报告。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 报告生成主函数
# ---------------------------------------------------------------------------


def generate_report(
    profile: dict,
    ranked_jobs: list[dict],
    strategy: dict,
    gaps: Optional[list[str]] = None,
    rewrites: Optional[list[dict]] = None,
    top_n: int = 5,
) -> str:
    """
    生成完整 Markdown 求职策略报告。

    参数：
      - profile: 学生画像（来自 Resume Parser Agent）
      - ranked_jobs: 已排序岗位列表（来自 Application Ranker Agent）
      - strategy: 策略包（来自 Strategy Planner Agent）
      - gaps: 能力缺口列表（可选，来自 Gap Diagnosis Agent）
      - rewrites: 简历改写建议（可选，来自 Resume Conversion Agent）
      - top_n: 报告中展示的岗位数量（默认 5）

    返回：
      - Markdown 格式字符串
    """
    parts = []

    # ---- 标题 + 基本信息 ----
    parts.append(_build_header(profile))
    parts.append("")

    # ---- 一、岗位投递优先级榜单 ----
    parts.append("## 一、岗位投递优先级榜单")
    parts.append("")
    parts.append(_build_job_table(ranked_jobs[:top_n]))
    parts.append("")

    # ---- 二、今日优先投递 Top3 ----
    parts.append("## 二、今日优先投递建议（Top 3）")
    parts.append("")
    parts.append(_build_priority_top3(strategy.get("priority_top3", [])))
    parts.append("")

    # ---- 三、稳妥 / 平衡 / 冲刺岗位组合 ----
    parts.append("## 三、岗位组合建议")
    parts.append("")
    parts.append(_build_job_combo(strategy.get("job_combo", {})))
    parts.append("")

    # ---- 四、能力缺口诊断 ----
    parts.append("## 四、能力缺口诊断")
    parts.append("")
    parts.append(_build_gaps(ranked_jobs[:top_n], gaps))
    parts.append("")

    # ---- 五、简历改写建议 ----
    parts.append("## 五、简历改写建议")
    parts.append("")
    parts.append(_build_rewrites(ranked_jobs[:top_n], rewrites))
    parts.append("")

    # ---- 六、7 天投递计划 ----
    parts.append("## 六、7 天投递执行计划")
    parts.append("")
    parts.append(_build_apply_plan(strategy.get("apply_plan_7day", [])))
    parts.append("")

    # ---- 七、面试准备计划 ----
    parts.append("## 七、7 天面试准备计划")
    parts.append("")
    parts.append(_build_interview_plan(strategy.get("interview_plan_7day", [])))
    parts.append("")

    # ---- 八、需要先改简历再投的岗位 ----
    resume_advice = strategy.get("resume_advice", [])
    if resume_advice:
        parts.append("")
        parts.append("## 八、需优先优化简历的岗位")
        parts.append("")
        parts.append(_build_resume_advice(resume_advice))
        parts.append("")

    # ---- 附录：学生画像摘要 ----
    parts.append("")
    parts.append("## 附录：学生画像摘要")
    parts.append("")
    parts.append(_build_profile_summary(profile))
    parts.append("")

    parts.append("---")
    parts.append(f"*报告生成时间：{date.today().strftime('%Y-%m-%d')} | 由 Offer 捕手 Agent 决策驾驶舱自动生成*")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 各小节构建函数
# ---------------------------------------------------------------------------

def _build_header(profile: dict) -> str:
    skills = "、".join(profile.get("skills", [])[:8]) or "待补充"
    return f"""# 📊 Offer 捕手 · 求职策略报告

**技能标签：** {skills}
"""


def _build_job_table(ranked_jobs: list[dict]) -> str:
    if not ranked_jobs:
        return "_暂无匹配岗位，请先运行匹配。_"

    lines = []
    lines.append("| 排名 | 岗位 | 公司 | 城市 | Match | Pass | Risk | Growth | 优先级 | 推荐动作 |")
    lines.append("|------|------|------|------|-------|------|------|---------|--------|----------|")

    action_map = {}
    for job in ranked_jobs:
        pass_s = job.get("pass_score", 50)
        risk_s = job.get("risk_score", 50)
        if pass_s >= 70 and risk_s <= 30:
            action = "✅ 立即投递"
        elif pass_s >= 55:
            action = "✏️ 先优化再投"
        elif job.get("growth_score", 50) >= 65:
            action = "🚀 冲刺岗位"
        else:
            action = "⏳ 暂缓"
        action_map[id(job)] = action

    for i, job in enumerate(ranked_jobs, 1):
        title = job.get("title", "未知岗位")
        company = job.get("company", "")
        city = job.get("city", "")
        match = job.get("match_score", job.get("score", 0))
        pass_s = job.get("pass_score", "-")
        risk_s = job.get("risk_score", "-")
        growth = job.get("growth_score", "-")
        priority = job.get("apply_priority", "-")
        action = action_map.get(id(job), "-")
        lines.append(f"| Top{i} | {title} | {company} | {city} | {match} | {pass_s} | {risk_s} | {growth} | {priority} | {action} |")

    return "\n".join(lines)


def _build_priority_top3(top3: list[dict]) -> str:
    if not top3:
        return "_请先运行匹配获取岗位推荐。_"
    lines = []
    for item in top3:
        lines.append(f"**Top {item['rank']}：{item['title']}（{item['company']}）**")
        lines.append(f"- 推荐动作：{item['apply_action']}")
        lines.append(f"- 理由：{item['reason']}")
        lines.append(f"- ApplyPriority = {item.get('apply_priority', '-')}，PassScore = {item.get('pass_score', '-')}，RiskScore = {item.get('risk_score', '-')}")
        lines.append("")
    return "\n".join(lines)


def _build_job_combo(combo: dict) -> str:
    if not combo:
        return "_暂无组合建议。_"
    lines = []
    emoji_map = {"稳妥岗（高通过率）": "🛡️", "平衡岗（综合推荐）": "⚖️", "冲刺岗（高成长价值）": "🚀"}
    for category, jobs in combo.items():
        emoji = emoji_map.get(category, "📌")
        lines.append(f"**{emoji} {category}**")
        if not jobs:
            lines.append("  （暂无）")
        for j in jobs:
            lines.append(f"  - {j.get('title', '')}（{j.get('company', '')}）| Match={j.get('match_score', '-')} Pass={j.get('pass_score', '-')} Risk={j.get('risk_score', '-')}")
        lines.append("")
    return "\n".join(lines)


def _build_gaps(ranked_jobs: list[dict], gaps: Optional[list[str]]) -> str:
    lines = []
    if gaps:
        for g in gaps[:6]:
            lines.append(f"- ⚠️ {g}")
    elif ranked_jobs:
        # 从第一个岗位的 gaps 字段取
        first_gaps = ranked_jobs[0].get("gaps", [])
        if first_gaps:
            for g in first_gaps:
                lines.append(f"- ⚠️ {g}")
        else:
            lines.append("_岗位能力缺口已纳入评分，暂无高风险项。_")
    else:
        lines.append("_请先运行匹配。_")
    return "\n".join(lines) if lines else "_暂无数据。_"


def _build_rewrites(ranked_jobs: list[dict], rewrites: Optional[list[dict]]) -> str:
    lines = []
    # 优先用传入的 rewrites，否则从 Top1 岗位取
    items = rewrites or (ranked_jobs[0].get("rewrites", []) if ranked_jobs else [])
    if not items:
        return "_暂无改写建议，简历与岗位匹配度较好。_"
    for item in items:
        before = item.get("before", "")
        after = item.get("after", "")
        lines.append(f"**原表达：**")
        lines.append(f"> {before}")
        lines.append(f"**建议改写：**")
        lines.append(f"> {after}")
        lines.append("")
    return "\n".join(lines)


def _build_apply_plan(plan: list[str]) -> str:
    if not plan:
        return "_暂无投递计划。_"
    return "\n".join(f"- {p}" for p in plan)


def _build_interview_plan(plan: list[str]) -> str:
    if not plan:
        return "_暂无面试准备计划。_"
    return "\n".join(f"- {p}" for p in plan)


def _build_resume_advice(advice: list[dict]) -> str:
    lines = []
    for item in advice[:5]:
        lines.append(f"**{item['title']}（{item['company']}）** — 紧急度：{item.get('urgency', '中')}")
        for tip in item.get("advice", []):
            lines.append(f"  - {tip}")
        lines.append("")
    return "\n".join(lines) if lines else "_所有岗位简历匹配度较好，可直接投递。_"


def _build_profile_summary(profile: dict) -> str:
    lines = []
    skills = "、".join(profile.get("skills", [])) or "未检测到明显技能词"
    project_sigs = "、".join(profile.get("project_signals", profile.get("project_signals", []))) or "未检测到项目信号"
    lines.append(f"- **技能：** {skills}")
    lines.append(f"- **项目信号：** {project_sigs}")
    lines.append(f"- **量化指标：** {'有 ✅' if profile.get('has_metrics') else '缺少 ⚠️'}（建议在简历中补充 NDCG/HitRate 等具体数字）")
    lines.append(f"- **LLM 项目信号：** {'有 ✅' if profile.get('has_llm_project') else '无 ⚠️'}（大模型方向建议补充 RAG/Agent 项目描述）")
    lines.append(f"- **推荐项目信号：** {'有 ✅' if profile.get('has_rec_project') else '无 ⚠️'}（推荐方向建议补充召回/排序项目描述）")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 保存报告到文件
# ---------------------------------------------------------------------------

def save_report(md_text: str, output_path: str | Path) -> Path:
    """
    将 Markdown 报告保存到指定路径，返回实际保存的 Path 对象。
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md_text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI 入口（方便本地测试）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 构造一个假数据结构用于测试报告格式
    dummy_profile = {
        "skills": ["Python", "PyTorch", "Transformer", "RAG", "Agent", "Embedding"],
        "project_signals": ["RAG", "Agent", "检索", "推荐", "Semantic ID"],
        "has_metrics": True,
        "has_llm_project": True,
        "has_rec_project": True,
    }
    dummy_jobs = [
        {
            "title": "大模型应用算法实习生",
            "company": "腾讯云智能",
            "city": "深圳",
            "direction": "大模型应用算法",
            "score": 92,
            "match_score": 92,
            "pass_score": 78,
            "risk_score": 22,
            "growth_score": 85,
            "apply_priority": 88,
            "gaps": ["建议补充 Agent 工具调用失败兜底方案", "简历缺少多轮对话评估指标"],
            "rewrites": [
                {"before": "做过 RAG Demo。", "after": "基于 bge embedding + FAISS 构建企业知识库问答，Top5 命中率提升 18%，并设计 Agent 工具调用链路。"}
            ],
        },
        {
            "title": "LLM 推荐算法实习生",
            "company": "内容平台事业群",
            "city": "北京",
            "direction": "推荐算法",
            "score": 85,
            "match_score": 85,
            "pass_score": 65,
            "risk_score": 40,
            "growth_score": 90,
            "apply_priority": 76,
            "gaps": [],
            "rewrites": [],
        },
    ]
    dummy_strategy = {
        "priority_top3": [
            {"rank": 1, "title": "大模型应用算法实习生", "company": "腾讯云智能", "apply_action": "先优化再投", "reason": "PassScore=78，建议补齐 Agent 项目证据再投。", "apply_priority": 88, "pass_score": 78, "risk_score": 22},
        ],
        "job_combo": {
            "稳妥岗（高通过率）": [{"title": "大模型应用算法实习生", "company": "腾讯云智能", "match_score": 92, "pass_score": 78, "risk_score": 22, "growth_score": 85}],
            "平衡岗（综合推荐）": [{"title": "LLM 推荐算法实习生", "company": "内容平台事业群", "match_score": 85, "pass_score": 65, "risk_score": 40, "growth_score": 90}],
            "冲刺岗（高成长价值）": [],
        },
        "apply_plan_7day": [f"第 {i} 天：投递执行 + 简历优化。" for i in range(1, 8)],
        "interview_plan_7day": [f"第 {i} 天：面试准备。" for i in range(1, 8)],
        "resume_advice": [],
    }

    md = generate_report(dummy_profile, dummy_jobs, dummy_strategy)
    out = Path(__file__).resolve().parent.parent / "reports"
    saved = save_report(md, out / "求职策略报告_测试.md")
    print(f"测试报告已保存到：{saved}")
