"""
Offer 捕手 v3 — LangGraph 5 Agent Supervisor 模式
架构：JobAnalyzer → ResumeReviewer → ResumeOptimizer → CareerCoach
"""
from __future__ import annotations
import sys, os, time
from html import escape
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from graph import run_pipeline
from file_parser import extract_text_from_upload

AGENTS = ["JobAnalyzer", "ResumeReviewer", "ResumeOptimizer", "CareerCoach"]


def inject_css():
    st.markdown("""<style>
:root{--ink:#e5e7eb;--muted:#9ca3af;--line:#374151;--bg:#0f1117;--card:#1a1d2e;--card2:#1f2235;--accent:#8b5cf6;--green:#10b981;--orange:#f59e0b;--red:#ef4444}
html,body,.stApp{background:var(--bg);color:var(--ink)}
.block-container{max-width:1100px;padding:1rem 1.5rem 2rem}
#MainMenu,footer,header{visibility:hidden}
div[data-testid="stToolbar"]{display:none}
section[data-testid="stSidebar"]{background:var(--card);border-right:1px solid var(--line)}
.stTextArea textarea,.stTextInput input{background:var(--card2)!important;color:var(--ink)!important;border-color:var(--line)!important}
.stButton>button{border-radius:10px;font-weight:750;min-height:44px}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#8b5cf6,#3b82f6);border:0}
.stExpander{border:1px solid var(--line)!important;border-radius:12px!important;background:var(--card)!important}
.stExpander [data-testid="stExpanderToggle"] svg{fill:var(--ink)!important}

.rpt-header{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 22px;margin-bottom:14px}
.rpt-title{font-size:22px;font-weight:900}
.rpt-title span{color:var(--accent)}
.rpt-meta{color:var(--muted);font-size:12px;margin-top:2px}

.rpt-timeline{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.rpt-tl-step{padding:5px 12px;border-radius:8px;font-size:11px;font-weight:800;background:#1f2937;color:#6b7280;border:1px solid var(--line)}
.rpt-tl-done{background:#064e3b;border-color:#10b981;color:#10b981}

.rpt-section{margin-bottom:20px}
.rpt-section-title{font-size:16px;font-weight:900;color:var(--ink);margin-bottom:10px}
.rpt-brief{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 20px}
.rpt-brief-row{display:flex;gap:28px;flex-wrap:wrap;margin-top:10px}
.rpt-brief-stat .num{font-size:26px;font-weight:950;line-height:1.1}
.rpt-brief-stat .label{font-size:11px;color:var(--muted);font-weight:700}
.rpt-direction{display:inline-block;background:rgba(139,92,246,.15);border:1px solid rgba(139,92,246,.3);color:var(--accent);border-radius:8px;padding:6px 12px;font-weight:800;font-size:13px;margin-top:6px}
.rpt-today{background:var(--card2);border-radius:10px;padding:10px 14px;margin-top:12px;font-size:13px;line-height:1.7}

.rpt-portfolio{display:flex;gap:14px;flex-wrap:wrap}
.rpt-pf-col{flex:1;min-width:200px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.rpt-pf-col.safe{border-top:3px solid var(--green)}
.rpt-pf-col.stretch{border-top:3px solid var(--orange)}
.rpt-pf-col.hold{border-top:3px solid var(--red)}
.rpt-pf-col h3{font-size:14px;font-weight:900;margin-bottom:10px}
.rpt-pf-item{padding:6px 8px;border-radius:6px;margin-bottom:4px;font-size:13px}
.rpt-pf-item:hover{background:var(--card2)}
.rpt-pf-item .pf-title{font-weight:750}
.rpt-pf-item .pf-company{color:var(--muted);font-size:11px}

.rpt-jd-card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px}
.rpt-jd-header{display:flex;justify-content:space-between;gap:12px}
.rpt-jd-header .score{font-size:26px;font-weight:950;min-width:60px;text-align:center}
.rpt-ev-block{margin-bottom:12px}
.rpt-ev-block h5{font-size:12px;font-weight:800;margin-bottom:4px}
.rpt-ev-source{font-size:11px;color:var(--muted);background:var(--card2);border-radius:6px;padding:6px 10px}
.rpt-ev-hit{background:rgba(16,185,129,.1);color:var(--green);padding:5px 8px;border-radius:4px;font-size:12px;margin:2px 0}
.rpt-ev-gap{background:rgba(245,158,11,.1);color:var(--orange);padding:5px 8px;border-radius:4px;font-size:12px;margin:2px 0}

.rpt-whatif{display:flex;gap:12px;flex-wrap:wrap}
.rpt-whatif-item{flex:1;min-width:200px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;text-align:center}
.rpt-whatif-gain{font-size:30px;font-weight:950;color:var(--green)}
.rpt-whatif-action{font-size:13px;font-weight:750;margin-top:6px}
.rpt-whatif-why{font-size:11px;color:var(--muted);margin-top:4px}

.rpt-action-item{display:flex;align-items:center;gap:10px;background:var(--card2);border-radius:8px;padding:8px 12px;margin:4px 0;font-size:12px}
.rpt-badge{font-size:10px;font-weight:800;padding:3px 8px;border-radius:6px;white-space:nowrap}
.rpt-badge.green{background:rgba(16,185,129,.15);color:var(--green)}
.rpt-badge.orange{background:rgba(245,158,11,.15);color:var(--orange)}

.rpt-empty{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:40px;text-align:center;color:var(--muted)}
.rpt-footer{text-align:center;color:#4b5563;font-size:11px;padding:20px 0 8px}

@media(max-width:960px){.rpt-portfolio{flex-direction:column}}
</style>""", unsafe_allow_html=True)


def sidebar() -> dict:
    with st.sidebar:
        st.header("📄 简历")
        up = st.file_uploader("上传 TXT/MD/PDF/DOCX", type=["txt","md","pdf","docx"])
        if up and up.name != st.session_state.get("_up",""):
            with st.spinner("解析..."):
                txt, msg = extract_text_from_upload(up)
            if txt:
                st.session_state.resume_text = txt
                st.session_state._up = up.name
                st.success(msg)

        default = st.session_state.get("resume_text","")
        if not default:
            default = "张三 | 大模型应用算法工程师\n2022.09-2026.06 XX大学 计算机科学\n实习: LoRA微调Qwen2.5 + RAG知识库(FAISS)\n项目: Offer捕手 9Agent匹配系统 NDCG@10=0.87\n技能: Python PyTorch Transformers LangChain FAISS"
        resume = st.text_area("简历文本", value=default, height=200, label_visibility="collapsed")
        goal = st.text_input("目标", placeholder="如: 找大模型应用算法实习, 深圳/北京")
        st.divider()
        run = st.button("开始 Agent 分析", type="primary", use_container_width=True)
    return {"resume": resume, "goal": goal, "run": run}


def main():
    st.set_page_config(page_title="Offer 捕手 v3", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
    inject_css()
    for k, v in {"ran": False, "report": None, "resume_text": ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    args = sidebar()

    if args["run"]:
        with st.spinner("Supervisor 调度 Agent 团队中..."):
            _do_run(args["resume"], args["goal"])

    # Header
    st.markdown("<div class='rpt-header'><div class='rpt-title'>Offer 捕手 <span>v3 · Supervisor 模式</span></div><div class='rpt-meta'>LangGraph 5 Agent · JobAnalyzer → ResumeReviewer → ResumeOptimizer → CareerCoach</div></div>", unsafe_allow_html=True)

    if not st.session_state.ran:
        st.markdown("<div class='rpt-empty'>粘贴简历后点「开始 Agent 分析」，Supervisor 调度 4 个 Agent 协作完成决策报告。</div>", unsafe_allow_html=True)
        return

    r = st.session_state.report
    if not r: return

    intent = r.intent_summary
    pf = r.portfolio
    jds = r.job_decisions[:8]

    # Timeline
    steps = ""
    for a in AGENTS:
        steps += f"<span class='rpt-tl-step rpt-tl-done'>{a}</span>"
    st.markdown(f"<div class='rpt-timeline'>{steps}</div>", unsafe_allow_html=True)

    # Decision Brief
    st.markdown("<div class='rpt-section-title'>📋 决策摘要</div>", unsafe_allow_html=True)
    st.markdown(f"""<div class='rpt-brief'>
    <span class='rpt-direction'>🎯 {escape(intent.target_role)} · {escape(intent.stage)}</span>
    <div class='rpt-brief-row'>
    <div class='rpt-brief-stat'><div class='num'>{len(r.jd_sources)}</div><div class='label'>JD</div></div>
    <div class='rpt-brief-stat'><div class='num'>{len(jds)}</div><div class='label'>匹配</div></div>
    <div class='rpt-brief-stat'><div class='num'>{len(pf.safe)}</div><div class='label'>稳投</div></div>
    <div class='rpt-brief-stat'><div class='num'>{len(pf.stretch)}</div><div class='label'>冲刺</div></div>
    <div class='rpt-brief-stat'><div class='num'>{len(pf.hold)}</div><div class='label'>暂缓</div></div>
    </div>
    <div class='rpt-today'><b>今日建议：</b>先投 {len(pf.safe)} 个稳投岗，边优化简历边投 {len(pf.stretch)} 个冲刺岗。{len(pf.hold)} 个岗位暂不投。</div>
    </div>""", unsafe_allow_html=True)

    # Portfolio
    st.markdown("<div class='rpt-section-title'>📊 岗位组合</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpt-portfolio'>", unsafe_allow_html=True)
    for col_class, col_label, jobs in [("safe","✅ 稳投",pf.safe), ("stretch","🚀 冲刺",pf.stretch), ("hold","⏸ 暂缓",pf.hold)]:
        st.markdown(f"<div class='rpt-pf-col {col_class}'><h3>{col_label}</h3>", unsafe_allow_html=True)
        for j in jobs[:4]:
            st.markdown(f"<div class='rpt-pf-item'><div class='pf-title'>{escape(j.title)}</div><div class='pf-company'>{escape(j.company)} · 匹配 {j.match_score:.0f}</div></div>", unsafe_allow_html=True)
        if not jobs: st.markdown("<div style='color:var(--muted);font-size:12px'>暂无</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Evidence Board
    st.markdown(f"<div class='rpt-section-title'>🔬 岗位证据（{len(jds)} 个）</div>", unsafe_allow_html=True)
    for i, jd in enumerate(jds):
        pct = max(0, min(100, int(jd.match_score)))
        color = "var(--green)" if pct >= 70 else ("var(--orange)" if pct >= 50 else "var(--red)")
        with st.expander(f"#{i+1} {escape(jd.title)} @ {escape(jd.company)} · {jd.decision} · 匹配 {pct}", expanded=(i==0)):
            jdsrc = next((s for s in r.jd_sources if s.title == jd.title), None)

            # Source
            st.markdown("<div class='rpt-ev-block'><h5>📡 JD 来源</h5></div>", unsafe_allow_html=True)
            if jdsrc:
                st.markdown(f"""<div class='rpt-ev-source'>
                <b>{escape(jdsrc.source_type)}</b> · {escape(jdsrc.city)} · {escape(jdsrc.salary)}<br>
                {escape(jdsrc.raw_snippet[:150])}...</div>""", unsafe_allow_html=True)

            # Evidence
            st.markdown("<div class='rpt-ev-block'><h5>🔬 命中证据</h5></div>", unsafe_allow_html=True)
            for ev in jd.resume_evidence[:4]:
                st.markdown(f"<div class='rpt-ev-hit'>✓ {escape(ev)}</div>", unsafe_allow_html=True)

            # Gaps
            if jd.missing_evidence:
                st.markdown("<div class='rpt-ev-block'><h5>⚠️ 缺口</h5></div>", unsafe_allow_html=True)
                for gap in jd.missing_evidence[:4]:
                    st.markdown(f"<div class='rpt-ev-gap'>✗ {escape(gap)}</div>", unsafe_allow_html=True)

            # Actions
            if jd.resume_actions:
                st.markdown("<div class='rpt-ev-block'><h5>📝 建议</h5></div>", unsafe_allow_html=True)
                for a in jd.resume_actions:
                    badge_cls = "green" if a.evidence_based else "orange"
                    badge_label = "可改写" if a.evidence_based else "需先补经历"
                    st.markdown(f"<div class='rpt-action-item'><span class='rpt-badge {badge_cls}'>{badge_label}</span> {escape(a.target_text[:100])}</div>", unsafe_allow_html=True)

    # What-if
    if r.what_if_plan:
        st.markdown("<div class='rpt-section-title'>🔄 如果补这些技能……</div>", unsafe_allow_html=True)
        st.markdown("<div class='rpt-whatif'>", unsafe_allow_html=True)
        for wi in r.what_if_plan:
            gain = wi.expected_gain.split('+')[-1] if '+' in wi.expected_gain else wi.expected_gain
            st.markdown(f"""<div class='rpt-whatif-item'>
            <div class='rpt-whatif-gain'>+{escape(gain)}</div>
            <div class='rpt-whatif-action'>{escape(wi.action)}</div>
            <div class='rpt-whatif-why'>{escape(wi.why)} · {escape(wi.needed_time)}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Trace
    with st.expander("🔍 Agent 执行日志", expanded=False):
        for t in r.trace: st.caption(escape(t))

    st.markdown("<div class='rpt-footer'>Offer 捕手 v3 · LangGraph Supervisor 5 Agent · 所有结论有源可查</div>", unsafe_allow_html=True)


def _do_run(resume, goal):
    ss = st.session_state
    try:
        report = run_pipeline(resume, goal)
        ss.report = report
        ss.ran = True
    except Exception as e:
        st.error(f"分析失败: {e}")
        import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
