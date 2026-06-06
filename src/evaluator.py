"""
evaluator.py — Eval 框架执行器（v2：Match / Priority 分离评估）
"""
from __future__ import annotations

import json, re, sys, time
from pathlib import Path
from typing import Any, Optional

from src.eval_schema import (
    EvalTrace, ERROR_TAXONOMY, detect_errors, load_golden_cases,
    compute_ndcg, compute_mrr, golden_case_to_relevance,
)


# ---------------------------------------------------------------------------
# Agent 流程条配置
# ---------------------------------------------------------------------------

AGENTS = [
    {"key": "profile", "name": "Profile Builder", "desc": "解析简历 → 学生画像", "icon": "👤"},
    {"key": "jd", "name": "JD Intelligence", "desc": "解析 JD → 岗位画像", "icon": "📋"},
    {"key": "scout", "name": "Opportunity Scout", "desc": "召回候选岗位池", "icon": "🔍"},
    {"key": "ranker", "name": "Application Ranker", "desc": "计算 Match/Pass/Risk/Growth", "icon": "📊"},
    {"key": "gap", "name": "Gap Diagnosis", "desc": "能力缺口 + 简历风险", "icon": "⚠️"},
    {"key": "conversion", "name": "Resume Conversion", "desc": "简历改写建议", "icon": "✏️"},
    {"key": "strategy", "name": "Strategy Planner", "desc": "投递策略 + 7 天计划", "icon": "🗺️"},
]

STATUS_ICONS = {"completed": "✅", "running": "⏳", "pending": "⬜"}

# 技术选型说明（底部折叠）
_TECH_EXPLANATION = """
**项目定位：基于多 Agent 协作的大模型应用算法系统**（不是商业 HR 工具）。

---

### 一、多 Agent 如何分工

| Agent | 职责 | LLM 是否参与 |
|---|---|---|
| Profile Builder | 简历 → 结构化画像 | 可选（理解非结构化文本） |
| JD Intelligence | JD → 结构化岗位画像 | 可选（归一化技能表述） |
| Opportunity Scout | 关键词/TF-IDF 召回候选池 | 否（保证稳定可解释） |
| Application Ranker | 多维度加权公式计算排序 | 否（**排序必须可解释**） |
| Gap Diagnosis | 规则检测能力缺口 | 可选（生成可读解释） |
| Resume Conversion | 规则约束的简历改写 | 可选（语言优化） |
| Strategy Planner | 规则策略 + 自然语言总结 | 可选（总结生成） |

**核心设计：LLM 是"可选增强层"，非依赖项。无 API Key 时所有 Agent 仍可完整运行。**

---

### 二、为什么排序/决策用可解释公式，而不是黑盒 LLM 打分？

1. **可解释性约束**：面试官/用户需要知道"为什么推荐这个岗位"，黑盒 LLM 打分无法回答
2. **权重可调试**：`ApplyPriority = 0.40×Match + 0.30×Pass - 0.15×Risk + 0.15×Growth`，每个权重都有业务含义
3. **稳定性**：LLM API 可能抖动，排序公式稳定可复现
4. **数据效率**：公式不需要标注数据，LLM 微调才需要

---

### 三、语义召回为什么用轻量模型（bge-small-zh）而不是满血 LLM？

1. **延迟**：LLM 调用 ~200ms，嵌入模型 ~20ms
2. **成本**：嵌入模型本地运行，LLM API 按 token 计费
3. **稳定性**：嵌入模型输出稳定，LLM 可能返回不一致相似度
4. **可解释性**：嵌入向量可以可视化（t-SNE），LLM 相似度是黑盒

---

### 四、Eval/Error Analysis 如何保证系统质量？

1. **Golden Cases**：8 个核心 case（覆盖同方向/跨方向/不同城市/不同风险偏好）
2. **Error Taxonomy**：10 类错误（E1–E10），每类有自动检测逻辑
3. **指标**：Top1 Acc、Recall@5、NDCG@5、MRR@5
4. **持续迭代**：每次修改排序公式后跑 eval，确保不降低核心指标

---

### 五、为什么项目强调"算法深度"而不是"功能完整"？

1. **求职目标**：算法岗位（大模型应用算法/LLM 应用算法/Agent 算法）
2. **核心叙事**：排序公式设计、语义召回优化、证据链构建、Eval/Error Analysis 迭代
3. **技术深度**：不是"调包侠"，而是"算法设计者"
4. **差异化**：大多数 Demo 项目只做"功能完整"，我们做"算法深度"

---
"""

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_case(case: dict, jobs_path: str | Path) -> tuple[Any, list[dict], dict]:
    """运行单个 golden case，返回 (trace, errors, metrics)。"""
    if EvalTrace is None:
        raise RuntimeError("eval_schema.py not loaded")

    trace = EvalTrace()
    trace.case_id = case.get("case_id", "unknown")
    trace.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    trace.resume_text = case.get("resume_text", "")
    trace.target_role = case.get("target_role", "")
    trace.target_city = case.get("target_city", "")
    trace.stage = case.get("stage", "")

    errors: list[dict] = []

    # ---- read new golden labels ----
    exp_matches = set(case.get("expected_top_matches", []))
    exp_priorities = set(case.get("expected_top_priorities", []))
    exp_recall = set(case.get("expected_recall_jobs", []))
    exp_action = case.get("expected_action", "")

    # ---- Agent 1: Profile Builder ----
    t0 = time.time()
    profile: dict = {}
    try:
        from src.resume_parser import parse_resume
        profile = parse_resume(trace.resume_text)
    except Exception:
        pass
    # 注入用户目标偏好到 profile（供 StrategyPlanner 使用）
    if profile is None:
        profile = {}
    profile["_city"] = trace.target_city
    profile["_stage"] = trace.stage
    profile["_target_role"] = trace.target_role
    trace.profile_output = profile
    trace.agent_timings["profile"] = round(time.time() - t0, 3)

    # E1/E2
    if profile:
        actual = set(profile.get("skills", []))
        missed = set(case.get("expected_skills", [])) - actual
        if missed:
            errors.append({"code": "E1_PROFILE_MISS", "agent": "ProfileBuilder", "message": f"漏抽技能：{missed}", "severity": "high"})
        rl = trace.resume_text.lower()
        for s in actual:
            if s.lower() not in rl:
                errors.append({"code": "E2_PROFILE_HALLUCINATION", "agent": "ProfileBuilder", "message": f"可能幻觉技能：{s}", "severity": "high"})
                break

    # ---- Agent 3/4: Scout + Ranker ----
    t1 = time.time()
    scored: list[dict] = []
    try:
        from src.matcher import rank_jobs
        scored = rank_jobs(
            resume_text=trace.resume_text,
            profile=profile,
            target_role=trace.target_role,
            target_city=trace.target_city,
            stage=trace.stage,
            top_k=8,
            jobs_path=Path(jobs_path),
        )
    except Exception:
        pass
    trace.scout_candidates = scored
    trace.agent_timings["scout"] = round(time.time() - t1, 3)

    # construct both rankings
    by_match = sorted(scored, key=lambda x: x.get("match_score", 0), reverse=True)
    by_priority = sorted(scored, key=lambda x: x.get("apply_priority", 0), reverse=True)

    top5_m = [j.get("title", "") for j in by_match[:5]]
    top5_p = [j.get("title", "") for j in by_priority[:5]]
    top1_m = by_match[0].get("title", "") if by_match else ""
    top1_p = by_priority[0].get("title", "") if by_priority else ""

    # E4: recall miss (expected_recall_jobs not in ANY top5)
    if exp_recall:
        hit_recall = exp_recall & set(top5_m) or exp_recall & set(top5_p)
        if not hit_recall:
            errors.append({"code": "E4_RECALL_MISS", "agent": "OpportunityScout",
                           "message": f"expected_recall_jobs {exp_recall} 未进入任一 Top5", "severity": "high"})
    # E4_MATCH: expected_top_matches not in match top5
    if exp_matches and not (exp_matches & set(top5_m)):
        errors.append({"code": "E4_MATCH_RECALL_MISS", "agent": "OpportunityScout",
                       "message": f"expected_top_matches {exp_matches} 未进入 Match Top5: {top5_m}", "severity": "high"})
    # E4_PRIORITY: expected_top_priorities not in priority top5
    if exp_priorities and not (exp_priorities & set(top5_p)):
        errors.append({"code": "E4_PRIORITY_RECALL_MISS", "agent": "OpportunityScout",
                       "message": f"expected_top_priorities {exp_priorities} 未进入 Priority Top5: {top5_p}", "severity": "high"})

    # E5: rank misorder (top1 not in expected for each list)
    if exp_matches and top1_m and top1_m not in exp_matches:
        errors.append({"code": "E5_MATCH_RANK_MISORDER", "agent": "ApplicationRanker",
                       "message": f"Match Top1={top1_m}, expected {exp_matches}", "severity": "high"})
    if exp_priorities and top1_p and top1_p not in exp_priorities:
        errors.append({"code": "E5_PRIORITY_RANK_MISORDER", "agent": "ApplicationRanker",
                       "message": f"Priority Top1={top1_p}, expected {exp_priorities}", "severity": "high"})
    # E6: score calibration
    if by_priority:
        ms = by_priority[0].get("match_score", 0)
        ap = by_priority[0].get("apply_priority", 0)
        if isinstance(ms, (int,float)) and isinstance(ap, (int,float)) and ms < 30 and ap > 70:
            errors.append({"code": "E6_SCORE_CALIBRATION", "agent": "ApplicationRanker",
                               "message": f"Top1 match_score={ms:.1f} 过低但 apply_priority={ap:.1f} 过高", "severity": "medium"})

    trace.ranker_scores = {
        "top1_match_title": top1_m, "top1_priority_title": top1_p,
        "top5_match": top5_m, "top5_priority": top5_p,
    }

    # ---- Agent 5/6: Gap + Conversion ----
    t2 = time.time()
    # score_job() in matcher.py already called attach_conversion_scores(),
    # so conv_scored already has correct pass/risk/growth scores.
    conv_scored = scored

    gaps: list[str] = []
    rewrites: list[dict] = []
    for j in conv_scored:
        g = j.get("gaps", [])
        if isinstance(g, list):
            for item in g:
                if isinstance(item, str): gaps.append(item)
                elif isinstance(item, dict): gaps.append(item.get("skill", ""))
        r = j.get("rewrites", [])
        if isinstance(r, list):
            for item in r:
                if isinstance(item, dict): rewrites.append(item)
    trace.gap_diagnosis_output = {"gaps": gaps[:5]}
    trace.resume_conversion_output = {"rewrites": rewrites[:5]}

    # E7: gap diagnosis unsupported
    rl = trace.resume_text.lower()
    for gs in gaps:
        if isinstance(gs, str):
            from src.eval_schema import _extract_missing_terms_from_gap
            missing_terms = _extract_missing_terms_from_gap(gs)
            unsupported_terms = [term for term in missing_terms if term.lower() in rl]
            if unsupported_terms:
                errors.append({"code": "E7_GAP_UNSUPPORTED", "agent": "GapDiagnosis",
                               "message": f"缺口诊断称缺失技能「{unsupported_terms[0]}」，但简历中存在相关证据", "severity": "medium"})
                break
        elif isinstance(gs, dict):
            skill = gs.get("skill", "")
            if skill and skill.lower() in rl:
                errors.append({"code": "E7_GAP_UNSUPPORTED", "agent": "GapDiagnosis",
                               "message": f"缺口诊断称缺失技能「{skill}」，但简历中存在相关证据", "severity": "medium"})
                break

    # E8: rewrite overclaim
    for rw in rewrites:
        sl = rw.get("score_lift", 0)
        if isinstance(sl, (int,float)) and sl > 30:
            errors.append({"code": "E8_REWRITE_OVERCLAIM", "agent": "ResumeConversion",
                           "message": f"改写声称过大：{rw.get('original','')} -> +{sl}", "severity": "high"})
            break

    trace.agent_timings["conversion"] = round(time.time() - t2, 3)

    # ---- Agent 7: Strategy Planner ----
    t3 = time.time()
    strategy: dict = {}
    try:
        from src.strategy_planner import gen_strategy_package
        strategy = gen_strategy_package(conv_scored, profile)
    except Exception:
        strategy = {}
    trace.strategy_output = strategy
    trace.agent_timings["strategy"] = round(time.time() - t3, 3)

    # E9: strategy conflict
    top3 = strategy.get("priority_top3", [])
    actions = [t.get("apply_action", "") for t in top3]
    if "立即投递" in str(actions) and "暂缓" in str(actions):
        errors.append({"code": "E9_STRATEGY_CONFLICT", "agent": "StrategyPlanner",
                       "message": "投递策略冲突：同时建议立即投递和暂缓", "severity": "medium"})
    # E9_ACTION_MISMATCH: actual action vs expected
    actual_action = top3[0].get("apply_action", "") if top3 else ""
    if exp_action and actual_action and exp_action != actual_action:
        errors.append({"code": "E9_ACTION_MISMATCH", "agent": "StrategyPlanner",
                       "message": f"expected_action={exp_action}, actual_action={actual_action}", "severity": "medium"})

    # ---- Report ----
    t4 = time.time()
    try:
        from src.report_generator import generate_report
        generate_report(profile, conv_scored, strategy)
    except Exception:
        pass
    trace.agent_timings["report"] = round(time.time() - t4, 3)

    # ---- Metrics ----
    metrics = _compute_metrics(trace, case, by_match, by_priority, exp_matches, exp_priorities, exp_recall, exp_action, actual_action)

    # ---- detect_errors (supplemental) ----
    if detect_errors:
        extra = detect_errors(trace, case)
        existing = {e["code"] for e in errors}
        for ee in extra:
            if ee["code"] not in existing:
                errors.append(ee)
                existing.add(ee["code"])

    trace.errors = errors
    trace.overall_pass = len(errors) == 0
    trace.pass_reason = "" if trace.overall_pass else "; ".join(e["code"] for e in errors)
    trace.agent_metrics = metrics
    return trace, errors, metrics


def _compute_metrics(trace, case, by_match, by_priority, exp_matches, exp_priorities, exp_recall, exp_action, actual_action):
    """Compute metrics for a single case."""
    m = {}

    # Match
    t1m = by_match[0].get("title", "") if by_match else ""
    t5m = [j.get("title", "") for j in by_match[:5]]
    m["match_top1_hit"] = (t1m in exp_matches) if exp_matches else None
    m["match_recall_at_5"] = (len(exp_matches & set(t5m))/len(exp_matches)) if exp_matches else None

    # Priority
    t1p = by_priority[0].get("title", "") if by_priority else ""
    t5p = [j.get("title", "") for j in by_priority[:5]]
    m["priority_top1_hit"] = (t1p in exp_priorities) if exp_priorities else None
    m["priority_recall_at_5"] = (len(exp_priorities & set(t5p))/len(exp_priorities)) if exp_priorities else None

    # Recall (global)
    all5 = set(t5m) | set(t5p)
    m["recall_hit"] = (len(exp_recall & all5))/len(exp_recall) if exp_recall else None

    # Action
    m["action_hit"] = (exp_action == actual_action) if exp_action and actual_action else None
    m["expected_action"] = exp_action
    m["actual_action"] = actual_action

    # NDCG / MRR (需要 golden_case_to_relevance / compute_ndcg / compute_mrr）
    match_titles = [j.get("title", "") for j in by_match]
    pri_titles = [j.get("title", "") for j in by_priority]
    if golden_case_to_relevance:
        match_rel = golden_case_to_relevance(match_titles, case)
        pri_rel = golden_case_to_relevance(pri_titles, case)
        if match_rel and compute_ndcg:
            m["match_ndcg_5"] = round(compute_ndcg(match_rel, k=5), 4)
        if match_rel and compute_mrr:
            m["mrr_5"] = round(compute_mrr(match_rel, k=5), 4)
        if pri_rel and compute_ndcg:
            m["priority_ndcg_5"] = round(compute_ndcg(pri_rel, k=5), 4)

    m["top1_match_title"] = t1m
    m["top1_priority_title"] = t1p
    m["top5_match"] = t5m
    m["top5_priority"] = t5p
    m["expected_top_matches"] = list(exp_matches)
    m["expected_top_priorities"] = list(exp_priorities)
    m["expected_recall_jobs"] = list(exp_recall)
    # errors
    m["error_count"] = len(trace.errors)
    m["error_types"] = list({e["code"] for e in trace.errors})
    ae: dict[str, int] = {}
    for e in trace.errors:
        ae[e.get("agent", "?")] = ae.get(e.get("agent", "?"), 0) + 1
    m["agent_error_counts"] = ae
    return m


# ---------------------------------------------------------------------------
# Golden Case 管理
# ---------------------------------------------------------------------------

CORE_CASE_IDS = {f"case_{i:02d}" for i in range(1, 9)}


def _case_split(case: dict) -> str:
    """Return the evaluation split for a golden case."""
    explicit = case.get("eval_split")
    if explicit:
        return str(explicit)
    if "jd_text" in case:
        return "jd_intake"
    return "core" if case.get("case_id") in CORE_CASE_IDS else "stress"


def _should_run_case(case: dict, eval_split: str) -> bool:
    """Check if a case should be run."""
    if case.get("skip_eval"):
        return False
    if "jd_text" in case:
        return False
    split = _case_split(case)
    if eval_split == "all":
        return split in {"core", "stress"}
    return split == eval_split


def run_all_cases(golden_path: str|Path, jobs_path: str|Path, eval_split: str = "core"):
    """Run all golden cases and return traces + summary."""
    cases = load_golden_cases(golden_path)
    traces, all_errs, all_met = [], [], []
    for c in cases:
        if not _should_run_case(c, eval_split):
            continue
        t, err, met = run_case(c, jobs_path)
        traces.append(t); all_errs.extend(err); all_met.append(met)
    summary = _summarize(traces, all_errs, all_met)
    summary["eval_split"] = eval_split
    return traces, summary


def _summarize(traces, all_errs, all_met):
    """Summarize eval results."""
    n = len(traces)
    if n == 0: return {"total_cases": 0}

    def _avg(seq):
        valid = [x for x in seq if x is not None]
        return round(sum(valid)/len(valid), 4) if valid else None

    return {
        "total_cases": n,
        "pass_cases": sum(1 for t in traces if t.overall_pass),
        "pass_rate": round(sum(1 for t in traces if t.overall_pass)/n, 4),
        "match_top1_acc": _avg([m.get("match_top1_hit") for m in all_met]),
        "priority_top1_acc": _avg([m.get("priority_top1_hit") for m in all_met]),
        "action_acc": _avg([m.get("action_hit") for m in all_met]),
        "match_recall_at_5": _avg([m.get("match_recall_at_5") for m in all_met]),
        "priority_recall_at_5": _avg([m.get("priority_recall_at_5") for m in all_met]),
        "error_counts": {c: sum(1 for e in all_errs if e["code"]==c) for c in sorted({e["code"] for e in all_errs})},
        "agent_error_counts": dict(__import__("collections").Counter(e.get("agent", "?") for e in all_errs)),
    }


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_eval_report(traces, summary, output_path):
    """Generate eval report (Markdown)."""
    lines = ["# Eval Report (v2: Match/Priority split)", "",
             f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    lines += ["## Summary", "",
              f"| Metric | Value |", "|---|---|",
              f"| Eval split | {summary.get('eval_split','core')} |",
              f"| Total cases | {summary.get('total_cases','-')} |",
              f"| Pass cases | {summary.get('pass_cases','-')} |",
              f"| Pass rate | {round(summary.get('pass_rate',0)*100,1)}% |",
              f"| Match Top1 Acc | {_pct(summary.get('match_top1_acc'))} |",
              f"| Priority Top1 Acc | {_pct(summary.get('priority_top1_acc'))} |",
              f"| Action Acc | {_pct(summary.get('action_acc'))} |",
              f"| Match Recall@5 | {_pct(summary.get('match_recall_at_5'))} |",
              f"| Priority Recall@5 | {_pct(summary.get('priority_recall_at_5'))} |", ""]
    ec = summary.get("error_counts", {})
    if ec:
        lines += ["## Error Taxonomy", "",
                  "| Code | Count | Agent | Severity |", "|---|---|---|---|"]
        for code, cnt in sorted(ec.items(), key=lambda x:-x[1]):
            tax = (ERROR_TAXONOMY or {}).get(code, {})
            lines.append(f"| {code} | {cnt} | {tax.get('agent','-')} | {tax.get('severity','-')} |")
        lines.append("")
    ae = summary.get("agent_error_counts", {})
    if ae:
        lines += ["## Agent-level Errors", "", "| Agent | Count |", "|---|---|"]
        for a, c in sorted(ae.items(), key=lambda x:-x[1]):
            lines.append(f"| {a} | {c} |")
        lines.append("")
    lines += ["## Per-Case Results", ""]
    for i, t in enumerate(traces, 1):
        lines += [f"### Case {i}: {t.case_id}", ""]
        m = t.agent_metrics
        lines += [f"- Target: {t.target_role} | City: {t.target_city} | Stage: {t.stage}",
                  f"- Match Top1: {m.get('top1_match_title','-')} | Expected: {m.get('expected_top_matches',[])}",
                  f"- Priority Top1: {m.get('top1_priority_title','-')} | Expected: {m.get('expected_top_priorities',[])}",
                  f"- Action: actual={m.get('actual_action','-')}, expected={m.get('expected_action','-')}",
                  f"- Match Top1 Hit: {m.get('match_top1_hit','-')} | Priority Top1 Hit: {m.get('priority_top1_hit','-')}",
                  f"- Errors({len(t.errors)}): " + (", ".join(e["code"] for e in t.errors) if t.errors else "none")]
        if t.errors:
            for e in t.errors:
                lines.append(f"  - `{e['code']}`: {e['message']}")
        lines.append("")
    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
    return content


def generate_error_analysis(traces, summary, output_path):
    """Generate error analysis report."""
    lines = ["# Error Analysis (v2: Match/Priority split)", "",
             f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    ec = summary.get("error_counts", {})
    lines += ["## Error Ranking", ""]
    if ec:
        lines += ["| Rank | Code | Count | Agent |", "|---|---|---|---|"]
        for rank, (code, cnt) in enumerate(sorted(ec.items(), key=lambda x:-x[1]), 1):
            tax = (ERROR_TAXONOMY or {}).get(code, {})
            lines.append(f"| {rank} | {code} | {cnt} | {tax.get('agent','-')} |")
    else:
        lines.append("[OK] No errors.")
        lines.append("")

    # Root cause analysis
    total = summary.get("total_cases", 0)
    pass_cases = summary.get("pass_cases", 0)
    match_top1 = summary.get("match_top1_acc")
    priority_top1 = summary.get("priority_top1_acc")

    lines += ["## Root Cause: Matcher vs Label", ""]
    lines.append(f"- Pass rate: {pass_cases}/{total} ({round(summary.get('pass_rate',0)*100,1)}%)")
    lines.append(f"- Match Top1 Acc: {_pct(match_top1)}")
    lines.append(f"- Priority Top1 Acc: {_pct(priority_top1)}")
    lines.append("")

    # E4 analysis
    e4_match = ec.get("E4_MATCH_RECALL_MISS", 0)
    e4_pri = ec.get("E4_PRIORITY_RECALL_MISS", 0)
    e4 = ec.get("E4_RECALL_MISS", 0)
    lines += ["## E4 Recall Miss Analysis", ""]
    if e4 or e4_match or e4_pri:
        lines.append(f"- E4_MATCH_RECALL_MISS: {e4_match} | E4_PRIORITY_RECALL_MISS: {e4_pri} | E4_RECALL_MISS: {e4}")
        lines.append("")
        lines.append("**Possible causes:**")
        lines.append("1. If E4_MATCH_RECALL_MISS > 0: match_score is too low for expected roles — skill keyword coverage insufficient or expected label not aligned with jobs.json")
        lines.append("2. If E4_PRIORITY_RECALL_MISS > 0: apply_priority is too low for expected roles — risk_score is pulling down the priority (by design)")
        lines.append("3. If E4_RECALL_MISS > 0: expected_recall_jobs has jobs not in the top5 of either list — check if the job title exists in jobs.json")
        lines.append("")
    else:
        lines.append("[OK] No recall issues.")
        lines.append("")

    # E5 analysis
    e5_match = ec.get("E5_MATCH_RANK_MISORDER", 0)
    e5_pri = ec.get("E5_PRIORITY_RANK_MISORDER", 0)
    lines += ["## E5 Rank Misorder Analysis", ""]
    if e5_match or e5_pri:
        lines.append(f"- E5_MATCH_RANK_MISORDER: {e5_match} | E5_PRIORITY_RANK_MISORDER: {e5_pri}")
        lines.append("")
        lines.append("**Diagnosis per case:**")
        for t in traces:
            errs = [e["code"] for e in t.errors]
            if "E5_MATCH_RANK_MISORDER" in errs or "E5_PRIORITY_RANK_MISORDER" in errs:
                m = t.agent_metrics
                lines.append(f"- **{t.case_id}**: Match Top1={m.get('top1_match_title','-')}, Expected Match={m.get('expected_top_matches',[])}, Priority Top1={m.get('top1_priority_title','-')}, Expected Pri={m.get('expected_top_priorities',[])}")
        lines.append("")
        lines.append("**Verdict:**")
        if e5_match > 0:
            lines.append("- E5_MATCH errors: matcher's match_score weights may need tuning, OR expected_top_matches label is unreasonable")
        if e5_pri > 0:
            lines.append("- E5_PRIORITY errors: apply_priority incorporates risk/pass scores — this is intentional, not a bug. If expected_top_priorities should be about pure match, adjust labels.")
        lines.append("")
    else:
        lines.append("[OK] No rank issues.")
        lines.append("")

    # case_02 analysis
    lines += ["## Case_02 (Recommendation Algorithm) Analysis", ""]
    case02 = [t for t in traces if t.case_id == "case_02"]
    if case02:
        t = case02[0]
        m = t.agent_metrics
        errs = [e["code"] for e in t.errors]
        lines.append(f"- Expected: {m.get('expected_top_matches',[])}")
        lines.append(f"- Match Top1: {m.get('top1_match_title','-')}")
        lines.append(f"- Match Top5: {m.get('top5_match',[])}")
        lines.append(f"- Errors: {errs if errs else 'none'}")
        if "E5_MATCH_RANK_MISORDER" in errs or "E4_MATCH_RECALL_MISS" in errs:
            lines.append("- **Diagnosis**: jobs.json has 'LLM 推荐算法实习生', not '推荐算法实习生'. The expectation (pure recommendation) and actual jobs (LLM + recommendation hybrid) may differ in match_score.")
            lines.append("- **Action**: Either adjust expected_top_matches to 'LLM 推荐算法实习生' (if that's acceptable), or acknowledge that pure rec roles don't exist in current job pool.")
        else:
            lines.append("- [OK] No recall/rank issues for case_02 after fixing job title alignment.")
        lines.append("")

    # case_03, case_08 analysis
    lines += ["## Case_03/08 (NLP/CV -> LLM Transfer) Analysis", ""]
    for cid in ["case_03", "case_08"]:
        ct = [t for t in traces if t.case_id == cid]
        if ct:
            t = ct[0]; m = t.agent_metrics; errs = [e["code"] for e in t.errors]
            lines.append(f"**{cid}**: Errors={errs if errs else 'none'}, Match Top1={m.get('top1_match_title','-')}, Priority Top1={m.get('top1_priority_title','-')}")
    lines.append("")
    lines.append("**Diagnosis:**")
    lines.append("- case_03 (NLP -> LLM): Has NLP fundamentals but missing RAG/Agent skills. match_score may be reasonable but mismatched roles could rank higher.")
    lines.append("- case_08 (CV -> LLM): No LLM skills at all. Expected labels are empty (no good match). If system still suggests an LLM role, it means the ranking is over-optimistic for untransferable skill sets.")
    lines.append("- **Recommendation**: Adjust GrowthScore/RiskScore to reflect transfer difficulty more aggressively for case_08.")
    lines.append("")

    # Next steps
    lines += ["## Next Steps", ""]
    lines.append("1. If E5_MATCH errors persist: tune SKILL_KEYWORDS or match weight in matcher.py")
    lines.append("2. If E5_PRIORITY errors persist: review whether expected_top_priorities should be about pure match (then fix labels) or risk-adjusted priority (then matcher is correct)")
    lines.append("3. Expand jobs.json with more diverse roles (pure rec, pure CV) to test edge cases better")
    lines.append("4. Add more golden cases for transfer-learning scenarios (X background -> LLM role)")
    lines.append("")

    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
    return content


def _pct(val):
    """Format a float as percentage."""
    if val is None: return "N/A"
    return f"{round(val*100,1)}%"


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main_cli():
    """CLI entry point for eval."""
    import argparse
    ap = argparse.ArgumentParser(description="Offer Catcher Eval v2")
    ap.add_argument("--golden", default="eval/golden_cases.json")
    ap.add_argument("--jobs", default="data/jobs.json")
    ap.add_argument("--report", default="reports/eval_report.md")
    ap.add_argument("--error-analysis", default="reports/error_analysis.md")
    ap.add_argument("--split", choices=["core", "stress", "all"], default="core")
    args = ap.parse_args()
    Path(args.error_analysis).parent.mkdir(parents=True, exist_ok=True)
    traces, summary = run_all_cases(args.golden, args.jobs, eval_split=args.split)
    print(f"EVAL_CASES={summary.get('total_cases',0)}")
    print(f"PASS_CASES={summary.get('pass_cases',0)}")
    print(f"PASS_RATE={summary.get('pass_rate',0)}")
    print(f"MATCH_TOP1_ACC={_pct(summary.get('match_top1_acc'))}")
    print(f"PRIORITY_TOP1_ACC={_pct(summary.get('priority_top1_acc'))}")
    print(f"ACTION_ACC={_pct(summary.get('action_acc'))}")
    print(f"MATCH_RECALL_AT_5={_pct(summary.get('match_recall_at_5'))}")
    print(f"PRIORITY_RECALL_AT_5={_pct(summary.get('priority_recall_at_5'))}")
    ec = summary.get('error_counts', {})
    print(f"ERROR_COUNTS={ec}")
    generate_eval_report(traces, summary, args.report)
    print(f"[OK] Report: {args.report}")
    generate_error_analysis(traces, summary, args.error_analysis)
    print(f"[OK] Error Analysis: {args.error_analysis}")
    return traces, summary


if __name__ == "__main__":
    main_cli()
