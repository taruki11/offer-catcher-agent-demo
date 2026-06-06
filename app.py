"""
Offer 捕手 v2 — Agent Decision Report
重写结果页：Decision Brief → Portfolio → Evidence Board → What-if Plan
"""
from __future__ import annotations
import sys, os, time, hashlib
from html import escape
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from langgraph_workflow import run_full_pipeline
from file_parser import extract_text_from_upload

AGENT_NAMES = ["意向推断", "岗位搜索", "JD解析", "证据提取", "匹配推理", "反事实", "简历优化", "面试准备", "投递策略"]


def inject_css() -> None:
    st.markdown("""
<style>
:root {
  --ink:#101828; --muted:#667085; --line:#e4e7ec; --bg:#f5f7fb;
  --white:#fff; --blue:#1677ff; --green:#10b981; --orange:#f59e0b; --red:#ef4444;
  --purple:#7c3aed; --purple-bg:#f5f3ff;
}
html,body,.stApp{background:var(--bg);color:var(--ink)}
.block-container{max-width:1200px;padding:1.2rem 1.8rem 2rem}
#MainMenu,footer,header{visibility:hidden}
div[data-testid="stToolbar"]{display:none}
section[data-testid="stSidebar"]{background:var(--white);border-right:1px solid var(--line)}

/* ====== REPORT HEADER ====== */
.rpt-header{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:20px 24px;margin-bottom:16px;box-shadow:0 4px 16px rgba(16,24,40,.04)}
.rpt-title{font-size:22px;font-weight:900;color:var(--ink)}
.rpt-title span{color:var(--purple);font-weight:900}
.rpt-meta{color:var(--muted);font-size:12px;margin-top:4px}

/* ====== SECTION ====== */
.rpt-section{margin-bottom:20px}
.rpt-section-title{font-size:17px;font-weight:900;color:var(--ink);margin-bottom:10px;display:flex;align-items:center;gap:8px}
.rpt-section-sub{color:var(--muted);font-size:12px;margin-bottom:12px}

/* ====== DECISION BRIEF ====== */
.rpt-brief{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:20px 24px;box-shadow:0 4px 16px rgba(16,24,40,.04)}
.rpt-brief-row{display:flex;gap:32px;flex-wrap:wrap;margin-top:12px}
.rpt-brief-stat{min-width:100px}
.rpt-brief-stat .num{font-size:28px;font-weight:950;color:var(--ink);line-height:1.1}
.rpt-brief-stat .label{font-size:12px;color:var(--muted);font-weight:700}
.rpt-direction{display:inline-flex;align-items:center;gap:8px;background:var(--purple-bg);border:1px solid #c4b5fd;color:var(--purple);border-radius:10px;padding:8px 14px;font-weight:800;font-size:14px;margin-top:8px}
.rpt-today-advice{background:#f8fafc;border-radius:10px;padding:12px 16px;margin-top:14px;font-size:13px;line-height:1.7;color:var(--ink)}

/* ====== AGENT TIMELINE ====== */
.rpt-timeline{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:14px 20px;box-shadow:0 4px 16px rgba(16,24,40,.04)}
.rpt-timeline-row{display:flex;gap:6px;flex-wrap:wrap}
.rpt-tl-step{padding:5px 10px;border-radius:8px;font-size:11px;font-weight:800;background:#f3f4f6;color:#9ca3af;border:1px solid var(--line)}
.rpt-tl-done{background:#ecfdf3;border-color:#a7f3d0;color:#047857}

/* ====== PORTFOLIO ====== */
.rpt-portfolio{display:flex;gap:16px;flex-wrap:wrap}
.rpt-portfolio-col{flex:1;min-width:220px;background:var(--white);border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:0 4px 16px rgba(16,24,40,.04)}
.rpt-portfolio-col h3{font-size:15px;font-weight:900;margin-bottom:12px}
.rpt-portfolio-col.safe{border-top:3px solid var(--green)}
.rpt-portfolio-col.safe h3{color:var(--green)}
.rpt-portfolio-col.stretch{border-top:3px solid var(--orange)}
.rpt-portfolio-col.stretch h3{color:var(--orange)}
.rpt-portfolio-col.hold{border-top:3px solid var(--red)}
.rpt-portfolio-col.hold h3{color:var(--red)}
.rpt-pf-item{padding:8px 10px;border-radius:8px;margin-bottom:6px;font-size:13px;line-height:1.5;cursor:default}
.rpt-pf-item:hover{background:#f8fafc}
.rpt-pf-item .title{font-weight:750}
.rpt-pf-item .company{color:var(--muted);font-size:12px}
.rpt-pf-item .reason{font-size:11px;color:var(--muted);margin-top:2px}

/* ====== EVIDENCE BOARD ====== */
.rpt-jd-card{background:var(--white);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:12px;box-shadow:0 4px 14px rgba(16,24,40,.035)}
.rpt-jd-card:hover{border-color:#c4b5fd}
.rpt-jd-header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;cursor:pointer}
.rpt-jd-header .left{flex:1}
.rpt-jd-header .score{font-size:28px;font-weight:950;text-align:center;min-width:64px}
.rpt-jd-body{display:none;margin-top:14px;padding-top:14px;border-top:1px solid var(--line)}
.rpt-jd-body.open{display:block}
.rpt-ev-block{margin-bottom:14px}
.rpt-ev-block h5{font-size:13px;font-weight:800;color:var(--ink);margin-bottom:4px}
.rpt-ev-source{font-size:12px;color:var(--muted);background:#f9fafb;border-radius:8px;padding:8px 12px}
.rpt-ev-item{font-size:12px;padding:6px 10px;border-radius:6px;margin:3px 0}
.rpt-ev-hit{background:#ecfdf3;color:#027a48}
.rpt-ev-gap{background:#fffbeb;color:#92400e}
.rpt-ev-action{background:#eff6ff;color:#1d4ed8}
.rpt-ev-action-need-exp{background:#fef2f2;color:#b91c1c}
.rpt-ev-link{font-size:12px;color:var(--blue)}

/* ====== WHAT-IF ====== */
.rpt-whatif-item{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:8px;display:flex;align-items:center;gap:14px;box-shadow:0 2px 8px rgba(16,24,40,.02)}
.rpt-whatif-item:hover{border-color:var(--purple)}
.rpt-whatif-gain{font-size:26px;font-weight:950;color:var(--green);min-width:70px;text-align:center}
.rpt-whatif-body{flex:1}
.rpt-whatif-body .action{font-weight:800;font-size:14px}
.rpt-whatif-body .why{color:var(--muted);font-size:12px;margin-top:2px}

/* ====== ACTION QUEUE ====== */
.rpt-action-card{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:6px;display:flex;align-items:center;gap:12px;box-shadow:0 2px 8px rgba(16,24,40,.015)}
.rpt-action-badge{font-size:11px;font-weight:800;padding:4px 10px;border-radius:8px;white-space:nowrap}
.rpt-action-badge.rewrite{background:#ecfdf3;color:#027a48}
.rpt-action-badge.need-exp{background:#fffbeb;color:#92400e}
.rpt-action-badge.no-fake{background:#fef2f2;color:#b91c1c}

/* ====== BUTTON ====== */
.stButton>button{border-radius:10px;font-weight:750;min-height:44px}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#7c3aed,#0ea5e9);border:0;box-shadow:0 10px 22px rgba(124,58,237,.22)}

@media(max-width:960px){.rpt-portfolio{flex-direction:column}.rpt-brief-row{flex-direction:column;gap:16px}}
</style>""", unsafe_allow_html=True)


def render_sidebar() -> dict:
    with st.sidebar:
        st.header("📄 简历")
        uploaded = st.file_uploader("上传 TXT/MD/PDF/DOCX", type=["txt","md","pdf","docx"])
        if uploaded and uploaded.name != st.session_state.get("_up_name", ""):
            with st.spinner("解析中..."):
                text, msg = extract_text_from_upload(uploaded)
            if text:
                st.session_state.resume_text = text
                st.session_state._up_name = uploaded.name
                st.success(msg)

        default = st.session_state.get("resume_text", "")
        if not default:
            default = "张三 | 大模型应用算法工程师\n2022.09 - 2026.06  XX大学  计算机科学与技术  本科\n\n实习经历\n2025.06 - YY科技  算法实习生\n- LoRA 微调 Qwen2.5-7B\n- RAG 企业知识库问答系统（FAISS + Sentence Transformers）\n\n项目经历\nOffer捕手 — 多 Agent 求职匹配系统：9 Agent 协作，NDCG@10=0.87\n\n技能：Python, PyTorch, Transformers, LangChain, FAISS"
        resume = st.text_area("简历文本", value=default, height=230, label_visibility="collapsed")

        goal = st.text_input("目标", value="", placeholder="如：找大模型应用算法实习，深圳北京")

        with st.expander("⚙️ 设置", expanded=False):
            use_online = st.toggle("LLM 增强（~70s）", value=False, help="规则版秒出结果")
            top_n = st.slider("展示", 3, 15, 8)

        run = st.button("开始 Agent 分析", type="primary", use_container_width=True)
    return {"resume": resume, "goal": goal, "run": run, "use_online": use_online, "top_n": top_n}


def main():
    st.set_page_config(page_title="Offer 捕手 · Agent Report", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
    inject_css()
    for k, v in {"ran": False, "report": None, "resume_text": ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    args = render_sidebar()

    if args["run"]:
        with st.spinner("Agent 团队分析中..."):
            _run(args["resume"], args["goal"], args["use_online"])

    # ==================== 结果页 ====================
    if not st.session_state.ran:
        st.markdown("<div class='rpt-header'><div class='rpt-title'>Offer 捕手 <span>Agent Report</span></div><div class='rpt-meta'>左侧粘贴简历，9 个 Agent 协作生成可信决策报告</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='background:var(--white);border:1px solid var(--line);border-radius:16px;padding:48px 32px;text-align:center;color:var(--muted);font-size:14px'>等待分析开始……</div>", unsafe_allow_html=True)
        return

    report = st.session_state.report
    if not report: return

    intent = report.intent_summary
    pf = report.portfolio
    jds = report.job_decisions[:args["top_n"]]

    # ========== REPORT HEADER ==========
    st.markdown("<div class='rpt-header'><div class='rpt-title'>Offer 捕手 <span>Agent Report</span></div><div class='rpt-meta'>9 Agent 协作 · 所有结论有源可查 · {}</div></div>".format(report.generated_at[:19]), unsafe_allow_html=True)

    # ========== SECTION 1: DECISION BRIEF ==========
    st.markdown("<div class='rpt-section-title'>📋 求职决策摘要</div>", unsafe_allow_html=True)
    direction_label = f"{intent.target_role} · {intent.stage}"
    match_state = "方向匹配" if intent.confidence >= 0.6 else "信息不足，建议补充"

    today_count = len([j for j in jds if j.decision in ("立即投递","稳投","先优化再投")])
    need_improve = len([a for j in jds for a in j.resume_actions if not a.evidence_based])

    st.markdown(f"""
    <div class='rpt-brief'>
    <div><span class='rpt-direction'>🎯 {escape(direction_label)}</span>&nbsp;&nbsp;
        <span style='font-size:13px;color:var(--muted)'>· {match_state} · 置信度 {intent.confidence:.0%}</span></div>
    <div class='rpt-brief-row'>
        <div class='rpt-brief-stat'><div class='num'>{len(report.jd_sources)}</div><div class='label'>读取 JD</div></div>
        <div class='rpt-brief-stat'><div class='num'>{len(jds)}</div><div class='label'>有效匹配</div></div>
        <div class='rpt-brief-stat'><div class='num'>{len(pf.safe)}</div><div class='label'>稳投</div></div>
        <div class='rpt-brief-stat'><div class='num'>{len(pf.stretch)}</div><div class='label'>冲刺</div></div>
        <div class='rpt-brief-stat'><div class='num'>{len(pf.hold)}</div><div class='label'>暂缓</div></div>
        <div class='rpt-brief-stat'><div class='num'>{need_improve}</div><div class='label'>需补强项</div></div>
    </div>
    <div class='rpt-today-advice'>
    <b>今日建议：</b>
    先投 {today_count} 个稳投/冲刺岗{'，'}补强 {need_improve} 项经历后再投大厂岗。
    在「证据面板」中查看每个岗位为什么推荐、哪里还不够。
    </div>
    </div>""", unsafe_allow_html=True)

    # ========== SECTION 2: AGENT TIMELINE ==========
    st.markdown("<div class='rpt-section-title'>⏱ Agent 决策时间线</div>", unsafe_allow_html=True)
    steps_html = ""
    for i, name in enumerate(AGENT_NAMES):
        done = i < 9  # all done
        css = "rpt-tl-done" if done else ""
        steps_html += f"<span class='rpt-tl-step {css}'>{name}</span>"
    st.markdown(f"<div class='rpt-timeline'><div class='rpt-timeline-row'>{steps_html}</div></div>", unsafe_allow_html=True)

    # ========== SECTION 3: PORTFOLIO ==========
    st.markdown("<div class='rpt-section-title'>📊 岗位组合</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpt-section-sub'>按决策分级，不是按分数排列。</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpt-portfolio'>", unsafe_allow_html=True)

    # 稳投
    st.markdown("<div class='rpt-portfolio-col safe'><h3>✅ 稳投</h3>", unsafe_allow_html=True)
    for jd in (pf.safe or [])[:4]:
        st.markdown(f"""<div class='rpt-pf-item'>
        <div class='title'>{escape(jd.title)}</div>
        <div class='company'>{escape(jd.company)} · 匹配 {jd.match_score:.0f}</div>
        </div>""", unsafe_allow_html=True)
    if not (pf.safe or []): st.markdown("<div style='color:var(--muted);font-size:12px'>暂无</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 冲刺
    st.markdown("<div class='rpt-portfolio-col stretch'><h3>🚀 冲刺</h3>", unsafe_allow_html=True)
    for jd in (pf.stretch or [])[:4]:
        st.markdown(f"""<div class='rpt-pf-item'>
        <div class='title'>{escape(jd.title)}</div>
        <div class='company'>{escape(jd.company)} · 匹配 {jd.match_score:.0f}</div>
        </div>""", unsafe_allow_html=True)
    if not (pf.stretch or []): st.markdown("<div style='color:var(--muted);font-size:12px'>暂无</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 暂缓
    st.markdown("<div class='rpt-portfolio-col hold'><h3>⏸ 暂缓</h3>", unsafe_allow_html=True)
    for jd in (pf.hold or [])[:4]:
        reason_short = (jd.why_this_decision[0][:60] + "...") if jd.why_this_decision else ""
        st.markdown(f"""<div class='rpt-pf-item'>
        <div class='title'>{escape(jd.title)}</div>
        <div class='company'>{escape(jd.company)}</div>
        <div class='reason'>{escape(reason_short) if reason_short else '匹配度偏低'}</div>
        </div>""", unsafe_allow_html=True)
    if not (pf.hold or []): st.markdown("<div style='color:var(--muted);font-size:12px'>暂无</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # close portfolio

    # ========== SECTION 4: EVIDENCE BOARD ==========
    st.markdown(f"<div class='rpt-section-title'>🔬 岗位证据详情（{len(jds)} 个）</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpt-section-sub'>点开查看：JD 来源 → 简历证据 → 缺口 → 下一步行动</div>", unsafe_allow_html=True)

    for i, jd in enumerate(jds):
        pct = max(0, min(100, int(jd.match_score)))
        color = "#10b981" if pct >= 70 else ("#f59e0b" if pct >= 50 else "#ef4444")
        decision_label = jd.decision or "暂缓"

        with st.expander(f"#{i+1} {escape(jd.title)} @ {escape(jd.company)} · {decision_label} · 匹配 {pct}", expanded=False):
            # Block 1: JD Source
            st.markdown("<div class='rpt-ev-block'><h5>📡 JD 来源</h5></div>", unsafe_allow_html=True)
            jd_source = next((s for s in report.jd_sources if s.title == jd.title and s.company == jd.company), None)
            if jd_source:
                st.markdown(f"""
                <div class='rpt-ev-source'>
                <b>来源类型：</b>{escape(jd_source.source_type)}<br>
                <b>城市：</b>{escape(jd_source.city)} &nbsp; <b>薪资：</b>{escape(jd_source.salary)}<br>
                <b>JD 关键要求：</b>{escape(', '.join(jd_source.parsed_requirements[:6]) if jd_source.parsed_requirements else '（规则提取）')}<br>
                <b>JD 摘要：</b>{escape(jd_source.raw_snippet[:120])}...
                </div>""", unsafe_allow_html=True)
                if jd_source.source_url:
                    st.markdown(f"<a class='rpt-ev-link' href='{escape(jd_source.source_url)}' target='_blank'>🔗 原始链接</a>", unsafe_allow_html=True)

            # Block 2: Resume Evidence
            st.markdown("<div class='rpt-ev-block'><h5>🔬 简历证据（已命中）</h5></div>", unsafe_allow_html=True)
            if jd.resume_evidence:
                for ev in jd.resume_evidence:
                    st.markdown(f"<div class='rpt-ev-item rpt-ev-hit'>✓ {escape(ev)}</div>", unsafe_allow_html=True)
            else:
                st.caption("（请补充简历以提取更多证据）")

            # Block 3: Gaps
            st.markdown("<div class='rpt-ev-block'><h5>⚠️ 缺口判断</h5></div>", unsafe_allow_html=True)
            if jd.missing_evidence:
                for gap in jd.missing_evidence:
                    st.markdown(f"<div class='rpt-ev-item rpt-ev-gap'>✗ {escape(gap)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='rpt-ev-item rpt-ev-hit'>无明显缺口</div>", unsafe_allow_html=True)

            # Block 4: Actions
            st.markdown("<div class='rpt-ev-block'><h5>📝 下一步行动</h5></div>", unsafe_allow_html=True)
            if jd.resume_actions:
                for action in jd.resume_actions:
                    badge = "rewrite" if (action.evidence_based and action.action_type == "rewrite") else "need-exp"
                    badge_label = "可改写" if badge == "rewrite" else "需先补经历"
                    css_class = "rpt-ev-action" if badge == "rewrite" else "rpt-ev-action-need-exp"
                    st.markdown(f"""
                    <div class='rpt-action-card'>
                    <span class='rpt-action-badge {badge}'>{badge_label}</span>
                    <div style='flex:1;font-size:13px'>{escape(action.target_text[:120])}
                    <div style='font-size:11px;color:var(--muted)'>{escape(action.reason)}</div></div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("暂无建议")

    # ========== SECTION 5: WHAT-IF ==========
    if report.what_if_plan:
        st.markdown("<div class='rpt-section-title'>🔄 如果你补这些技能……（反事实模拟）</div>", unsafe_allow_html=True)
        for wi in report.what_if_plan:
            st.markdown(f"""
            <div class='rpt-whatif-item'>
            <div class='rpt-whatif-gain'>+{escape(wi.expected_gain.split('+')[-1] if '+' in wi.expected_gain else wi.expected_gain)}</div>
            <div class='rpt-whatif-body'>
            <div class='action'>{escape(wi.action)}</div>
            <div class='why'>{escape(wi.why)} · 预计 {escape(wi.needed_time)}</div>
            </div>
            </div>""", unsafe_allow_html=True)

    # ========== SECTION 6: ACTION QUEUE ==========
    all_rewrite = [a for j in jds for a in j.resume_actions if a.evidence_based and a.action_type == "rewrite"]
    all_need_exp = [a for j in jds for a in j.resume_actions if not a.evidence_based]
    if all_rewrite or all_need_exp:
        st.markdown("<div class='rpt-section-title'>📝 简历改写任务队列</div>", unsafe_allow_html=True)

        if all_rewrite:
            st.markdown("<div style='font-size:13px;font-weight:750;margin-bottom:6px;color:var(--green)'>🟢 可直接改写（简历已有证据）</div>", unsafe_allow_html=True)
            for a in all_rewrite[:4]:
                st.markdown(f"""
                <div class='rpt-action-card'>
                <span class='rpt-action-badge rewrite'>可改写</span>
                <div style='flex:1;font-size:13px'>{escape(a.target_text[:120])}</div>
                </div>""", unsafe_allow_html=True)

        if all_need_exp:
            st.markdown("<div style='font-size:13px;font-weight:750;margin:10px 0 6px;color:var(--orange)'>🟡 需要先补真实经历</div>", unsafe_allow_html=True)
            for a in all_need_exp[:4]:
                st.markdown(f"""
                <div class='rpt-action-card'>
                <span class='rpt-action-badge need-exp'>需先补经历</span>
                <div style='flex:1;font-size:13px'>{escape(a.target_text[:120])}
                <div style='font-size:11px;color:var(--muted)'>{escape(a.reason)}</div></div>
                </div>""", unsafe_allow_html=True)

    # ========== FOOTER ==========
    st.markdown("<div style='text-align:center;color:#98a2b3;font-size:12px;padding:20px 0 8px'>Offer 捕手 · Agent Report · 所有结论有源可查</div>", unsafe_allow_html=True)


def _run(resume: str, goal: str, use_online: bool):
    ss = st.session_state
    try:
        report = run_full_pipeline(resume, goal, use_online=use_online)
        ss.report = report
        ss.ran = True
    except Exception as e:
        st.error(f"分析失败: {e}")
        import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
