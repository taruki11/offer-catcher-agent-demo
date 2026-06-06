"""
LangGraph Agent 版本 - 把 ResumeParser、JDParser、Matcher、GapAnalyzer、StrategyPlanner 变成真正的图节点
包含状态管理、条件边、失败重试
"""
from __future__ import annotations

import json
import sys
import os
from typing import Any, Dict, List, Optional, TypedDict, Annotated, Literal
import operator

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END, START

# 导入现有模块（使用正确的函数名）
from src.resume_parser import parse_resume
from src.jd_parser import parse_jd
from src.matcher import rank_jobs, score_job
from src.conversion import attach_conversion_scores
from src.strategy_planner import gen_priority_top3

# ========== State 定义 ==========
class AgentState(TypedDict):
    """LangGraph Agent 状态"""
    
    # 输入
    resume_text: str
    jd_text: Optional[str]  # 可选：单个 JD 匹配模式
    jobs: list[dict]  # 岗位库
    
    # 解析结果
    profile: Optional[dict]  # ResumeParser 输出
    jd_parsed: Optional[dict]  # JDParser 输出（如果输入了 jd_text）
    
    # 匹配结果
    matched_jobs: Optional[list[dict]]  # Matcher 输出
    ranked_jobs: Optional[list[dict]]  # 排序后的岗位
    
    # 分析和策略
    gaps: Optional[list[dict]]  # GapAnalyzer 输出
    strategy: Optional[list[dict]]  # StrategyPlanner 输出
    
    # 状态控制
    current_step: str
    error: Optional[str]
    retry_count: int
    max_retries: int
    
    # 元数据
    trace: list[str]  # 执行轨迹（用于调试和可解释性）


# ========== Node 定义 ==========
def resume_parser_node(state: AgentState) -> AgentState:
    """简历解析节点"""
    print("[LangGraph] 📄 ResumeParser Node", file=sys.stderr)
    
    try:
        resume_text = state.get("resume_text", "")
        if not resume_text:
            state["error"] = "resume_text 为空"
            state["current_step"] = "error"
            return state
        
        # 调用现有模块
        profile = parse_resume(resume_text)
        
        state["profile"] = profile
        state["current_step"] = "resume_parsed"
        state["error"] = None
        state["trace"] = state.get("trace", []) + ["resume_parser: success"]
        
        print(f"[LangGraph] ✅ ResumeParser 完成: skills={len(profile.get('skills', []))}, has_llm_project={profile.get('has_llm_project', False)}", file=sys.stderr)
        
    except Exception as e:
        state["error"] = f"ResumeParser 失败: {str(e)}"
        state["current_step"] = "error"
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["trace"] = state.get("trace", []) + [f"resume_parser: error - {str(e)}"]
        print(f"[LangGraph] ❌ ResumeParser 失败: {e}", file=sys.stderr)
    
    return state


def jd_parser_node(state: AgentState) -> AgentState:
    """JD 解析节点（可选，如果输入了 jd_text）"""
    print("[LangGraph] 📋 JDParser Node", file=sys.stderr)
    
    try:
        jd_text = state.get("jd_text")
        
        # 如果没有 jd_text，跳过此节点
        if not jd_text:
            state["jd_parsed"] = None
            state["current_step"] = "jd_skipped"
            state["trace"] = state.get("trace", []) + ["jd_parser: skipped (no jd_text)"]
            print("[LangGraph] ⏭️ JDParser 跳过（无 jd_text）", file=sys.stderr)
            return state
        
        # 调用现有模块
        jd_parsed = parse_jd(jd_text)
        
        state["jd_parsed"] = jd_parsed
        state["current_step"] = "jd_parsed"
        state["error"] = None
        state["trace"] = state.get("trace", []) + ["jd_parser: success"]
        
        print(f"[LangGraph] ✅ JDParser 完成: title={jd_parsed.get('title', '')}, direction={jd_parsed.get('direction', '')}", file=sys.stderr)
        
    except Exception as e:
        state["error"] = f"JDParser 失败: {str(e)}"
        state["current_step"] = "error"
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["trace"] = state.get("trace", []) + [f"jd_parser: error - {str(e)}"]
        print(f"[LangGraph] ❌ JDParser 失败: {e}", file=sys.stderr)
    
    return state


def matcher_node(state: AgentState) -> AgentState:
    """岗位匹配节点"""
    print("[LangGraph] 🎯 Matcher Node", file=sys.stderr)
    
    try:
        profile = state.get("profile")
        jobs = state.get("jobs", [])
        jd_parsed = state.get("jd_parsed")
        
        if not profile:
            state["error"] = "profile 为空（ResumeParser 未执行）"
            state["current_step"] = "error"
            return state
        
        if not jobs:
            state["error"] = "jobs 岗位库为空"
            state["current_step"] = "error"
            return state
        
        # 如果是单个 JD 匹配模式
        if jd_parsed:
            # 把 jd_parsed 当成单个岗位，计算匹配分数
            job_with_score = score_job(jd_parsed, profile)
            state["matched_jobs"] = [job_with_score]
            state["ranked_jobs"] = [job_with_score]
            state["current_step"] = "matched_single"
            state["trace"] = state.get("trace", []) + ["matcher: single_jd_mode"]
            print(f"[LangGraph] ✅ Matcher 完成（单 JD 模式）: pass_score={job_with_score.get('pass_score', 0)}", file=sys.stderr)
        
        # 否则是批量匹配模式
        else:
            # 使用 rank_jobs 进行批量匹配
            resume_text = state.get("resume_text", "")
            ranked = rank_jobs(jobs, profile, resume_text)
            state["matched_jobs"] = ranked
            state["ranked_jobs"] = ranked[:10]  # Top 10
            state["current_step"] = "matched_batch"
            state["error"] = None
            state["trace"] = state.get("trace", []) + [f"matcher: batch_mode ({len(ranked)} jobs)"]
            
            print(f"[LangGraph] ✅ Matcher 完成（批量模式）: {len(ranked)} 个岗位匹配", file=sys.stderr)
        
    except Exception as e:
        state["error"] = f"Matcher 失败: {str(e)}"
        state["current_step"] = "error"
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["trace"] = state.get("trace", []) + [f"matcher: error - {str(e)}"]
        print(f"[LangGraph] ❌ Matcher 失败: {e}", file=sys.stderr)
    
    return state


def gap_analyzer_node(state: AgentState) -> AgentState:
    """差距分析节点"""
    print("[LangGraph] 🔍 GapAnalyzer Node", file=sys.stderr)
    
    try:
        profile = state.get("profile")
        ranked_jobs = state.get("ranked_jobs", [])
        
        if not profile or not ranked_jobs:
            state["error"] = "profile 或 ranked_jobs 为空"
            state["current_step"] = "error"
            return state
        
        # Gap 分析：对比简历和 Top3 岗位的要求
        gaps = []
        for i, job in enumerate(ranked_jobs[:3]):
            missing_skills = job.get("missing_skills", [])
            gaps.append({
                "rank": i + 1,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "missing_skills": missing_skills,
                "pass_score": job.get("pass_score", 0),
                "risk_score": job.get("risk_score", 0),
                "suggestions": [
                    f"补充技能: {skill}" for skill in missing_skills[:3]
                ],
            })
        
        state["gaps"] = gaps
        state["current_step"] = "gaps_analyzed"
        state["error"] = None
        state["trace"] = state.get("trace", []) + [f"gap_analyzer: {len(gaps)} gaps found"]
        
        print(f"[LangGraph] ✅ GapAnalyzer 完成: {len(gaps)} 个岗位差距分析", file=sys.stderr)
        
    except Exception as e:
        state["error"] = f"GapAnalyzer 失败: {str(e)}"
        state["current_step"] = "error"
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["trace"] = state.get("trace", []) + [f"gap_analyzer: error - {str(e)}"]
        print(f"[LangGraph] ❌ GapAnalyzer 失败: {e}", file=sys.stderr)
    
    return state


def strategy_planner_node(state: AgentState) -> AgentState:
    """策略规划节点"""
    print("[LangGraph] 🎯 StrategyPlanner Node", file=sys.stderr)
    
    try:
        ranked_jobs = state.get("ranked_jobs", [])
        profile = state.get("profile")
        
        if not ranked_jobs or not profile:
            state["error"] = "ranked_jobs 或 profile 为空"
            state["current_step"] = "error"
            return state
        
        # 调用现有模块生成 Top3 策略
        strategy = gen_priority_top3(ranked_jobs, profile)
        
        state["strategy"] = strategy
        state["current_step"] = "strategy_generated"
        state["error"] = None
        state["trace"] = state.get("trace", []) + [f"strategy_planner: {len(strategy)} strategies"]
        
        print(f"[LangGraph] ✅ StrategyPlanner 完成: {len(strategy)} 个岗位策略", file=sys.stderr)
        for s in strategy:
            print(f"  - {s['rank']}. {s['title']} @ {s['company']}: {s['apply_action']}", file=sys.stderr)
        
    except Exception as e:
        state["error"] = f"StrategyPlanner 失败: {str(e)}"
        state["current_step"] = "error"
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["trace"] = state.get("trace", []) + [f"strategy_planner: error - {str(e)}"]
        print(f"[LangGraph] ❌ StrategyPlanner 失败: {e}", file=sys.stderr)
    
    return state


def error_handler_node(state: AgentState) -> AgentState:
    """错误处理节点：决定是否重试或终止"""
    print("[LangGraph] 🚨 ErrorHandler Node", file=sys.stderr)
    
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if retry_count < max_retries:
        print(f"[LangGraph] 🔄 重试 {retry_count + 1}/{max_retries}", file=sys.stderr)
        state["retry_count"] = retry_count + 1
        state["trace"] = state.get("trace", []) + [f"error_handler: retry {retry_count + 1}/{max_retries}"]
        
        # 根据错误类型决定回退到哪个节点
        error = state.get("error", "")
        if "ResumeParser" in error:
            state["current_step"] = "resume_parser"
        elif "JDParser" in error:
            state["current_step"] = "jd_parser"
        elif "Matcher" in error:
            state["current_step"] = "matcher"
        elif "GapAnalyzer" in error:
            state["current_step"] = "gap_analyzer"
        elif "StrategyPlanner" in error:
            state["current_step"] = "strategy_planner"
        else:
            # 默认重试从 matcher 开始
            state["current_step"] = "matcher"
        
        return state
    else:
        print(f"[LangGraph] 🛑 达到最大重试次数 ({max_retries})，终止", file=sys.stderr)
        state["current_step"] = "failed"
        state["trace"] = state.get("trace", []) + [f"error_handler: max retries reached"]
        return state


# ========== 条件边函数 ==========
def should_continue(state: AgentState) -> Literal["jd_parser", "matcher", "gap_analyzer", "end", "error"]:
    """决定是否继续执行、报错或结束"""
    current_step = state.get("current_step", "")
    error = state.get("error")
    
    # 如果出错，进入错误处理
    if error and state.get("retry_count", 0) < state.get("max_retries", 3):
        return "error"
    
    # 如果达到最大重试次数，结束
    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return "end"
    
    # 根据当前步骤决定下一步
    if current_step == "resume_parsed":
        # 如果有 jd_text，先解析 JD；否则直接匹配
        return "jd_parser" if state.get("jd_text") else "matcher"
    elif current_step == "jd_parsed" or current_step == "jd_skipped":
        return "matcher"
    elif current_step == "matched_single" or current_step == "matched_batch":
        return "gap_analyzer"
    elif current_step == "gaps_analyzed":
        return "strategy_planner"
    elif current_step == "strategy_generated":
        return "end"
    elif current_step == "failed":
        return "end"
    else:
        return "end"


# ========== 构建 Graph ==========
def build_graph() -> StateGraph:
    """构建 LangGraph 状态机"""
    print("[LangGraph] 🏗️ 构建 Graph...", file=sys.stderr)
    
    # 创建 StateGraph
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("resume_parser", resume_parser_node)
    graph.add_node("jd_parser", jd_parser_node)
    graph.add_node("matcher", matcher_node)
    graph.add_node("gap_analyzer", gap_analyzer_node)
    graph.add_node("strategy_planner", strategy_planner_node)
    graph.add_node("error_handler", error_handler_node)
    
    # 添加边（普通边）
    graph.add_edge(START, "resume_parser")
    
    # 条件边：根据状态决定下一步
    graph.add_conditional_edges(
        "resume_parser",
        should_continue,
        {
            "jd_parser": "jd_parser",
            "matcher": "matcher",
            "error": "error_handler",
            "end": END,
        }
    )
    
    graph.add_conditional_edges(
        "jd_parser",
        should_continue,
        {
            "matcher": "matcher",
            "error": "error_handler",
            "end": END,
        }
    )
    
    graph.add_conditional_edges(
        "matcher",
        should_continue,
        {
            "gap_analyzer": "gap_analyzer",
            "error": "error_handler",
            "end": END,
        }
    )
    
    graph.add_conditional_edges(
        "gap_analyzer",
        should_continue,
        {
            "strategy_planner": "strategy_planner",
            "error": "error_handler",
            "end": END,
        }
    )
    
    graph.add_conditional_edges(
        "strategy_planner",
        should_continue,
        {
            "end": END,
            "error": "error_handler",
        }
    )
    
    # 错误处理的边
    graph.add_conditional_edges(
        "error_handler",
        should_continue,
        {
            "resume_parser": "resume_parser",
            "jd_parser": "jd_parser",
            "matcher": "matcher",
            "gap_analyzer": "gap_analyzer",
            "strategy_planner": "strategy_planner",
            "end": END,
        }
    )
    
    print("[LangGraph] ✅ Graph 构建完成", file=sys.stderr)
    
    return graph


# ========== 编译并运行 ==========
def run_agent(
    resume_text: str,
    jobs: list[dict],
    jd_text: Optional[str] = None,
    max_retries: int = 3,
) -> dict:
    """
    运行 LangGraph Agent
    
    Args:
        resume_text: 简历文本
        jobs: 岗位库列表
        jd_text: 可选，单个 JD 文本（用于 JD 匹配模式）
        max_retries: 最大重试次数
    
    Returns:
        dict: 包含 profile, strategy, gaps, trace 等
    """
    print("[LangGraph] 🚀 启动 Agent...", file=sys.stderr)
    
    # 构建 Graph
    graph = build_graph()
    app = graph.compile()
    
    # 初始状态
    initial_state = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "jobs": jobs,
        "profile": None,
        "jd_parsed": None,
        "matched_jobs": None,
        "ranked_jobs": None,
        "gaps": None,
        "strategy": None,
        "current_step": "start",
        "error": None,
        "retry_count": 0,
        "max_retries": max_retries,
        "trace": [],
    }
    
    # 运行 Graph
    final_state = app.invoke(initial_state)
    
    print(f"[LangGraph] ✅ Agent 完成，轨迹: {final_state.get('trace', [])}", file=sys.stderr)
    
    # 返回关键结果
    return {
        "profile": final_state.get("profile"),
        "strategy": final_state.get("strategy"),
        "gaps": final_state.get("gaps"),
        "matched_jobs": final_state.get("matched_jobs"),
        "ranked_jobs": final_state.get("ranked_jobs"),
        "trace": final_state.get("trace", []),
        "error": final_state.get("error"),
        "current_step": final_state.get("current_step"),
    }


# ========== 测试代码 ==========
if __name__ == "__main__":
    # 测试：加载样例简历和岗位库
    import json
    
    # 加载测试简历
    test_resume = """
    教育背景：XX大学 计算机科学 硕士 2024-2027
    项目经历：
    1. 基于 RAG 的简历匹配系统：使用 LLM + Embedding + FAISS 实现人岗匹配
    2. 推荐系统项目：使用 DeepFM 实现 CTR 预估，NDCG@5 提升 12%
    技能：Python, PyTorch, LLM, RAG, Agent, 推荐系统, Transformer
    """
    
    # 加载岗位库
    try:
        with open("data/jobs.json", "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except:
        jobs = []
    
    # 运行 Agent
    result = run_agent(test_resume, jobs, max_retries=3)
    
    print("\n" + "="*60)
    print("LangGraph Agent 运行结果")
    print("="*60)
    
    if result.get("profile"):
        print(f"Profile: {json.dumps(result['profile'], ensure_ascii=False, indent=2)}")
    
    if result.get("strategy"):
        print(f"\nStrategy ({len(result['strategy'])} 个岗位):")
        for s in result['strategy']:
            print(f"  {s['rank']}. {s['title']} @ {s['company']}: {s['apply_action']}")
    
    print(f"\nTrace: {result['trace']}")
    print(f"Error: {result['error']}")
    print(f"Current Step: {result['current_step']}")
    print("="*60)
