"""
eval_schema.py — Eval 框架数据结构 + Error Taxonomy
定义以下内容：
1. EvalTrace dataclass（单次运行 trace）
2. ERROR_TAXONOMY（E1–E10 错误类型定义）
3. AGENT_METRICS_SCHEMA（每个 Agent 的评估指标定义）
4. RAG_METRICS_SCHEMA（RAG/检索评估指标，仅底层能力）
5. detect_errors(trace) -> list[dict]（根据 trace 自动检测错误）
6. 辅助函数：load_golden_cases, compute_ndcg, compute_mrr, compute_recall_at_k, golden_case_to_relevance
"""

from __future__ import annotations

import json, re, time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# 1. EvalTrace — 单次运行 trace
# ---------------------------------------------------------------------------

@dataclass
class EvalTrace:
    """一次 golden case 运行的完整 trace。"""

    # 元信息
    run_id: str = ""
    case_id: str = ""
    timestamp: str = ""

    # 输入
    resume_text: str = ""
    target_role: str = ""
    target_city: str = ""
    stage: str = ""

    # Agent 输出
    profile_output: dict = field(default_factory=dict)
    jd_intelligence_output: list[dict] = field(default_factory=list)
    scout_candidates: list[dict] = field(default_factory=list)
    ranker_scores: dict = field(default_factory=dict)
    gap_diagnosis_output: dict = field(default_factory=dict)
    resume_conversion_output: dict = field(default_factory=dict)
    strategy_output: dict = field(default_factory=dict)

    # 指标
    agent_timings: dict = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)
    agent_metrics: dict = field(default_factory=dict)
    overall_pass: bool = False
    pass_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "case_id": self.case_id,
            "timestamp": self.timestamp,
            "input": {
                "resume_text": self.resume_text,
                "target_role": self.target_role,
                "target_city": self.target_city,
                "stage": self.stage,
            },
            "agent_outputs": {
                "profile": self.profile_output,
                "jd_intelligence": self.jd_intelligence_output,
                "scout_candidates": self.scout_candidates,
                "ranker_scores": self.ranker_scores,
                "gap_diagnosis": self.gap_diagnosis_output,
                "resume_conversion": self.resume_conversion_output,
                "strategy": self.strategy_output,
            },
            "agent_timings": self.agent_timings,
            "errors": self.errors,
            "agent_metrics": self.agent_metrics,
            "overall_pass": self.overall_pass,
            "pass_reason": self.pass_reason,
        }

    def to_json(self, fp: str | Path) -> None:
        Path(fp).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# 2. Error Taxonomy（E1–E10）
# ---------------------------------------------------------------------------

ERROR_TAXONOMY = {
    "E1_PROFILE_MISS": {
        "agent": "ProfileBuilder",
        "description": "简历画像漏抽关键技能/项目/指标",
        "severity": "high",
    },
    "E2_PROFILE_HALLUCINATION": {
        "agent": "ProfileBuilder",
        "description": "画像中出现了简历中不存在的技能/经历",
        "severity": "high",
    },
    "E3_JD_PARSE_ERROR": {
        "agent": "JDIntelligence",
        "description": "JD 解析错误：required_skills / hard_requirements 不完整",
        "severity": "medium",
    },
    "E4_RECALL_MISS": {
        "agent": "OpportunityScout",
        "description": "召回漏掉相关岗位（expected_recall_jobs 未进入任一 Top5）",
        "severity": "high",
    },
    "E4_MATCH_RECALL_MISS": {
        "agent": "OpportunityScout",
        "description": "匹配榜召回不足：expected_top_matches 未进入 Match Top5",
        "severity": "high",
    },
    "E4_PRIORITY_RECALL_MISS": {
        "agent": "OpportunityScout",
        "description": "优先级榜召回不足：expected_top_priorities 未进入 Priority Top5",
        "severity": "high",
    },
    "E5_RANK_MISORDER": {
        "agent": "ApplicationRanker",
        "description": "排序不合理：期望岗位排在后面（任一榜单）",
        "severity": "high",
    },
    "E5_MATCH_RANK_MISORDER": {
        "agent": "ApplicationRanker",
        "description": "Match 榜 Top1 不是 expected_top_matches",
        "severity": "high",
    },
    "E5_PRIORITY_RANK_MISORDER": {
        "agent": "ApplicationRanker",
        "description": "Priority 榜 Top1 不是 expected_top_priorities",
        "severity": "high",
    },
    "E6_SCORE_CALIBRATION": {
        "agent": "ApplicationRanker",
        "description": "分数校准不合理：MatchScore/PassScore/RiskScore 与直觉不符",
        "severity": "medium",
    },
    "E7_GAP_UNSUPPORTED": {
        "agent": "GapDiagnosis",
        "description": "能力缺口诊断无证据支持（简历中无此问题，却指出）",
        "severity": "medium",
    },
    "E8_REWRITE_OVERCLAIM": {
        "agent": "ResumeConversion",
        "description": "简历改写过度声称/编造经历",
        "severity": "high",
    },
    "E9_STRATEGY_CONFLICT": {
        "agent": "StrategyPlanner",
        "description": "投递策略冲突：7 天计划不可执行 / 稳妥/平衡/冲刺组合矛盾",
        "severity": "medium",
    },
    "E9_ACTION_MISMATCH": {
        "agent": "StrategyPlanner",
        "description": "实际投递动作与 expected_action 不一致",
        "severity": "medium",
    },
    "E10_REPORT_ERROR": {
        "agent": "ReportGenerator",
        "description": "报告生成错误：信息不一致/缺失关键结论",
        "severity": "low",
    },
}


# ---------------------------------------------------------------------------
# 3. Agent-level 评估指标定义
# ---------------------------------------------------------------------------

AGENT_METRICS_SCHEMA = {
    "ProfileBuilder": {
        "skill_coverage": {
            "type": "float",
            "description": "技能抽取覆盖率 = 命中已知技能数 / golden 中 expected_skills 数",
        },
        "project_metric_hit": {
            "type": "bool",
            "description": "项目指标（如 HitRate、NDCG）是否被正确识别",
        },
        "missed_project": {
            "type": "bool",
            "description": "是否漏掉简历中关键项目",
        },
        "has_hallucination": {
            "type": "bool",
            "description": "是否幻觉出简历中不存在的信息",
        },
    },
    "JDIntelligence": {
        "required_skills_completeness": {
            "type": "float",
            "description": "required_skills 抽取完整度（与人工标注对比）",
        },
        "hard_requirements_correct": {
            "type": "bool",
            "description": "hard_requirements（如学历/实习时长）是否识别正确",
        },
        "interview_topics_relevance": {
            "type": "float",
            "description": "interview_topics 是否与岗位高度相关",
        },
    },
    "OpportunityScout": {
        "recall_at_5": {
            "type": "float",
            "description": "Recall@5 = expected_top_jobs 中出现在 Top5 的比例",
        },
        "recall_at_3": {
            "type": "float",
            "description": "Recall@3",
        },
        "target_job_in_topk": {
            "type": "bool",
            "description": "目标岗位是否进入 TopK",
        },
        "irrelevant_job_count": {
            "type": "int",
            "description": "TopK 中与目标方向无关的岗位数",
        },
    },
    "ApplicationRanker": {
        "top1_correct": {
            "type": "bool",
            "description": "Top1 是否符合 expected_top_jobs",
        },
        "ndcg_at_5": {
            "type": "float",
            "description": "NDCG@5（以 expected_top_jobs 为 relelvance）",
        },
        "mrr_at_5": {
            "type": "float",
            "description": "MRR@5 = Mean Reciprocal Rank（第一个相关结果排名的倒数）",
        },
        "score_calibration_error": {
            "type": "float",
            "description": "分数校准误差：|预测匹配度 - 人工标注匹配度|",
        },
        "apply_priority_consistent": {
            "type": "bool",
            "description": "ApplyPriority 是否与风险偏好一致（高风险岗位不应排前）",
        },
    },
    "GapDiagnosis": {
        "true_gap_hit": {
            "type": "float",
            "description": "真实短板命中率（expected_missing_skills 中被指出比例）",
        },
        "unsupported_claim_count": {
            "type": "int",
            "description": "无证据批评的数量",
        },
        "missed_gap_count": {
            "type": "int",
            "description": "遗漏关键缺口数（expected_missing_skills 中未指出）",
        },
    },
    "ResumeConversion": {
        "keyword_coverage_lift": {
            "type": "float",
            "description": "改写后 JD 关键词覆盖率提升",
        },
        "has_fabrication": {
            "type": "bool",
            "description": "是否编造经历",
        },
        "ats_friendly": {
            "type": "bool",
            "description": "改写后是否更 ATS 友好（无表格/图片/特殊字符）",
        },
    },
    "StrategyPlanner": {
        "plan_executable": {
            "type": "bool",
            "description": "7 天计划是否可执行（每天任务量合理）",
        },
        "portfolio_balanced": {
            "type": "bool",
            "description": "稳妥/平衡/冲刺组合是否合理",
        },
        "no_conflict": {
            "type": "bool",
            "description": "是否存在先后矛盾（如同一天既投冲刺岗又投稳妥岗）",
        },
    },
}


# ---------------------------------------------------------------------------
# 4. RAG / 检索评估指标（仅底层能力，非项目主线）
# ---------------------------------------------------------------------------

RAG_METRICS_SCHEMA = {
    "recall_at_3": {
        "type": "float",
        "description": "Recall@3 = 相关 JD 在前 3 个检索结果中的比例",
    },
    "recall_at_5": {
        "type": "float",
        "description": "Recall@5 = 相关 JD 在前 5 个检索结果中的比例",
    },
    "mrr_at_5": {
        "type": "float",
        "description": "MRR@5 = Mean Reciprocal Rank（第一个相关结果排名的倒数）",
    },
    "ndcg_at_5": {
        "type": "float",
        "description": "NDCG@5 = 归一化折损累积增益",
    },
    "retrieval_supports_diagnosis": {
        "type": "bool",
        "description": "检索结果是否支持后续 Gap Diagnosis",
    },
    "fallback_when_no_results": {
        "type": "bool",
        "description": "检索不到时是否能 fallback（如返回空列表而不崩溃）",
    },
}


# ---------------------------------------------------------------------------
# 5. detect_errors(trace) -> list[dict]
# ---------------------------------------------------------------------------

def _extract_missing_terms_from_gap(gap_text: str) -> list[str]:
    """Extract concrete missing skills from a gap sentence.

    The gap generator writes strings such as:
    "岗位还要求 LLM 评估、数据分析，建议补充真实项目或技能证据。"

    E7 should only fire when a concrete missing term itself appears in the
    resume. Splitting the whole sentence creates false positives on generic
    words like LLM, 评估, 项目, etc.
    """
    if not isinstance(gap_text, str) or "岗位还要求" not in gap_text:
        return []
    match = re.search(r"岗位还要求\s*(.+?)(?:，|,|。|$)", gap_text)
    if not match:
        return []
    return [term.strip() for term in re.split(r"[、,，]", match.group(1)) if term.strip()]


def detect_errors(trace: EvalTrace, golden_case: dict) -> list[dict]:
    """
    根据 EvalTrace + golden_case 中的标注，自动检测错误。
    返回 list[dict]，每个 dict 包含：code, agent, message, severity
    """
    errors: list[dict] = []

    # ---- ProfileBuilder ----
    profile = trace.profile_output
    expected_skills = set(golden_case.get("expected_skills", []))
    actual_skills = set(profile.get("skills", []))

    # E1: 漏抽
    missed = expected_skills - actual_skills
    if missed:
        errors.append({
            "code": "E1_PROFILE_MISS",
            "agent": "ProfileBuilder",
            "message": f"漏抽技能：{missed}",
            "severity": "high",
        })

    # E2: 幻觉（检查画像中是否有简历中不存在的量化指标）
    resume_text = trace.resume_text.lower()
    for skill in actual_skills:
        if skill.lower() not in resume_text:
            errors.append({
                "code": "E2_PROFILE_HALLUCINATION",
                "agent": "ProfileBuilder",
                "message": f"可能幻觉技能：{skill}",
                "severity": "high",
            })
            break  # 只报一次

    # ---- OpportunityScout ----
    expected_jobs = set(golden_case.get("expected_top_jobs", []))
    actual_titles = [j.get("title", "") for j in trace.scout_candidates[:5]]
    actual_titles_set = set(actual_titles)

    if expected_jobs and not expected_jobs & actual_titles_set:
        errors.append({
            "code": "E4_RECALL_MISS",
            "agent": "OpportunityScout",
            "message": f"目标岗位 {expected_jobs} 未出现在 Top5：{actual_titles[:5]}",
            "severity": "high",
        })

    # ---- ApplicationRanker ----
    top1_title = ""
    if trace.scout_candidates:
        top1_title = trace.scout_candidates[0].get("title", "")

    # E5: Top1 不是 expected
    if expected_jobs and top1_title and top1_title not in expected_jobs:
        errors.append({
            "code": "E5_RANK_MISORDER",
            "agent": "ApplicationRanker",
            "message": f"Top1={top1_title}，但期望 {expected_jobs}",
            "severity": "high",
        })

    # E6: score calibration（简单启发：如果 match_score < 50 但排在 Top1，可能有问题）
    if trace.scout_candidates:
        top1 = trace.scout_candidates[0]
        ms = top1.get("match_score", 0)
        ps = top1.get("apply_priority", 0)
        if isinstance(ms, (int,float)) and isinstance(ps, (int,float)) and ms < 30 and ps > 70:
            errors.append({
                "code": "E6_SCORE_CALIBRATION",
                "agent": "ApplicationRanker",
                "message": f"Top1 match_score={ms:.1f} 过低但 apply_priority={ps:.1f} 过高",
                "severity": "medium",
            })

    # ---- GapDiagnosis ----
    gaps = trace.gap_diagnosis_output.get("gaps", [])
    expected_risks = set(golden_case.get("expected_risks", []))
    resume_text_lower = trace.resume_text.lower()

    # E7: 无证据批评（只检查结构化 gap 中明确列出的缺失技能）
    for gap_skill in gaps:
        if isinstance(gap_skill, str):
            missing_terms = _extract_missing_terms_from_gap(gap_skill)
            unsupported_terms = [term for term in missing_terms if term.lower() in resume_text_lower]
            if unsupported_terms:
                errors.append({
                    "code": "E7_GAP_UNSUPPORTED",
                    "agent": "GapDiagnosis",
                    "message": f"缺口诊断称缺失技能「{unsupported_terms[0]}」，但简历中存在相关证据",
                    "severity": "medium",
                })
                break
        elif isinstance(gap_skill, dict):
            skill = gap_skill.get("skill", "")
            if skill and skill.lower() in resume_text_lower:
                errors.append({
                    "code": "E7_GAP_UNSUPPORTED",
                    "agent": "GapDiagnosis",
                    "message": f"缺口诊断称缺失技能「{skill}」，但简历中存在相关证据",
                    "severity": "medium",
                })
                break

    # ---- ResumeConversion ----
    rewrites = trace.resume_conversion_output.get("rewrites", [])
    for rw in rewrites:
        new_text = rw.get("suggested", "")
        # 简单检查：如果建议文本包含简历中完全没有的技能词汇
        if new_text:
            # 检查是否过度声称（score 提升 > 30 分可能是过度包装）
            score_lift = rw.get("score_lift", 0)
            if isinstance(score_lift, (int,float)) and score_lift > 30:
                errors.append({
                    "code": "E8_REWRITE_OVERCLAIM",
                    "agent": "ResumeConversion",
                    "message": f"改写声称过大：{rw.get('original','')} -> +{score_lift}",
                    "severity": "high",
                })

    # ---- StrategyPlanner ----
    strategy = trace.strategy_output
    top3 = strategy.get("priority_top3", [])
    apply_actions = [t.get("apply_action", "") for t in top3]

    # E9: 策略冲突（同时出现"立即投递"和"暂缓"）
    if "立即投递" in str(apply_actions) and "暂缓" in str(apply_actions):
        errors.append({
            "code": "E9_STRATEGY_CONFLICT",
            "agent": "StrategyPlanner",
            "message": "投递策略冲突：同时建议立即投递和暂缓",
            "severity": "medium",
        })

    # E9_ACTION_MISMATCH: actual action vs expected
    actual_action = top3[0].get("apply_action", "") if top3 else ""
    expected_action = golden_case.get("expected_action", "")
    if expected_action and actual_action and expected_action != actual_action:
        errors.append({
            "code": "E9_ACTION_MISMATCH",
            "agent": "StrategyPlanner",
            "message": f"expected_action={expected_action}, actual_action={actual_action}",
            "severity": "medium",
        })

    # ---- Report ----
    # E10: 报告错误（检查报告是否包含关键信息）
    # 暂不实现，因为报告生成是可选的

    trace.errors = errors
    return errors


# ---------------------------------------------------------------------------
# 6. 辅助函数
# ---------------------------------------------------------------------------

def load_golden_cases(path: str | Path) -> list[dict]:
    """加载 eval/golden_cases.json。"""
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def compute_ndcg(relevances: list[float], k: int = 5) -> float:
    """
    计算 NDCG@k。
    relevances[i] = 第 i 个位置的 relevance score（0~1 或 0~5）。
    """
    import math

    def dcg(scores: list[float]) -> float:
        return sum(
            (2 ** s - 1) / math.log2(idx + 2)
            for idx, s in enumerate(scores[:k])
        )

    ideal = sorted(relevances, reverse=True)
    denom = dcg(ideal)
    return dcg(relevances) / denom if denom > 0 else 0.0


def compute_mrr(relevances: list[float], k: int = 5) -> float:
    """
    计算 MRR@k（Mean Reciprocal Rank）。
    返回第一个相关结果排名的倒数（1/rank），没有则返回 0.0。
    """
    for idx, s in enumerate(relevances[:k], start=1):
        if s > 0:
            return 1.0 / idx
    return 0.0


def compute_recall_at_k(
    retrieved: list[str], relevant: set[str], k: int
) -> float:
    """Recall@k = |retrieved[:k] ∩ relevant| / |relevant|。"""
    if not relevant:
        return 1.0
    hits = len(set(retrieved[:k]) & relevant)
    return hits / len(relevant)


def golden_case_to_relevance(
    retrieved_titles: list[str], golden_case: dict
) -> list[float]:
    """
    将 golden_case 中的 expected_top_jobs 转为 relevance list。
    命中 expected 的岗位 relevance=3，同类方向=2，其他=0。
    """
    expected = set(golden_case.get("expected_top_jobs", []))
    target_role = golden_case.get("target_role", "")

    relevances: list[float] = []
    for title in retrieved_titles:
        if title in expected:
            relevances.append(3.0)
        elif target_role and target_role in title:
            relevances.append(2.0)
        else:
            relevances.append(0.0)
    return relevances
