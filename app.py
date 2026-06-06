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
  --bg:#0c1016;
  --bg-soft:#10161f;
  --panel:#151c27;
  --panel-2:#1b2432;
  --panel-3:#202b3a;
  --ink:#f4f7fb;
  --ink-2:#d8e0ec;
  --muted:#9aa8ba;
  --line:rgba(226,232,240,.14);
  --line-strong:rgba(226,232,240,.24);
  --cyan:#4fd1c5;
  --blue:#60a5fa;
  --green:#34d399;
  --orange:#fbbf24;
  --red:#fb7185;
  --card-shadow:0 18px 45px rgba(0,0,0,.28);
}
html,body,.stApp{
  background:
    linear-gradient(135deg,#0c1016 0%,#111827 46%,#0e1820 100%) !important;
  color:var(--ink) !important;
}
.stApp *{letter-spacing:0}
.block-container{max-width:1220px;padding:1.35rem 1.8rem 2rem}
#MainMenu,footer,header{visibility:hidden}
div[data-testid="stToolbar"]{display:none}
section[data-testid="stSidebar"]{
  background:#0f141d !important;
  border-right:1px solid var(--line);
  box-shadow:12px 0 28px rgba(0,0,0,.18);
}
section[data-testid="stSidebar"] *{color:var(--ink-2) !important}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] label{
  color:var(--ink) !important;
}
section[data-testid="stSidebar"] p{color:var(--muted) !important}
textarea, input, div[data-baseweb="select"] > div{
  background:#0b1118 !important;
  color:var(--ink) !important;
  border:1px solid var(--line-strong) !important;
  border-radius:12px !important;
}
textarea:focus, input:focus{
  border-color:var(--cyan) !important;
  box-shadow:0 0 0 3px rgba(79,209,197,.16) !important;
}
div[data-testid="stFileUploader"] section{
  background:#0b1118 !important;
  border:1px dashed rgba(79,209,197,.35) !important;
  border-radius:14px !important;
}
div[data-testid="stExpander"]{
  background:rgba(255,255,255,.035) !important;
  border:1px solid var(--line) !important;
  border-radius:13px !important;
}
div[data-testid="stExpander"] details summary{
  color:var(--ink) !important;
  font-weight:800 !important;
}
details summary span[data-testid="stIconMaterial"]{
  font-size:0 !important;
  width:18px !important;
  height:18px !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  margin-right:4px !important;
}
details summary span[data-testid="stIconMaterial"]::before{
  content:"›";
  font-size:20px;
  line-height:1;
  color:var(--cyan);
  font-weight:900;
}
details[open] summary span[data-testid="stIconMaterial"]::before{
  content:"⌄";
}
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] span{
  color:inherit;
}

/* ====== REPORT HEADER ====== */
.rpt-header{
  background:linear-gradient(135deg,rgba(31,41,55,.96),rgba(12,20,30,.98));
  border:1px solid rgba(79,209,197,.28);
  border-radius:18px;
  padding:22px 26px;
  margin-bottom:18px;
  box-shadow:var(--card-shadow);
  position:relative;
  overflow:hidden;
}
.rpt-header:before{
  content:"";
  position:absolute;
  left:0;top:0;bottom:0;
  width:5px;
  background:linear-gradient(180deg,var(--cyan),var(--green));
}
.rpt-title{font-size:24px;font-weight:950;color:var(--ink) !important}
.rpt-title span{color:var(--cyan);font-weight:950}
.rpt-meta{color:var(--muted) !important;font-size:12px;margin-top:6px}

/* ====== SECTION ====== */
.rpt-section{margin-bottom:20px}
.rpt-section-title{
  font-size:18px;
  font-weight:950;
  color:var(--ink) !important;
  margin:22px 0 10px;
  display:flex;
  align-items:center;
  gap:8px;
}
.rpt-section-title:after{
  content:"";
  height:1px;
  flex:1;
  background:linear-gradient(90deg,var(--line-strong),transparent);
}
.rpt-section-sub{color:var(--muted) !important;font-size:12px;margin-bottom:12px}

/* ====== DECISION BRIEF ====== */
.rpt-brief{
  background:linear-gradient(180deg,var(--panel),#111923);
  border:1px solid var(--line);
  border-radius:18px;
  padding:22px 24px;
  box-shadow:var(--card-shadow);
}
.rpt-brief-row{display:flex;gap:32px;flex-wrap:wrap;margin-top:12px}
.rpt-brief-stat{
  min-width:106px;
  padding:12px 14px;
  border-radius:14px;
  background:rgba(255,255,255,.045);
  border:1px solid rgba(255,255,255,.07);
}
.rpt-brief-stat .num{font-size:30px;font-weight:950;color:var(--ink) !important;line-height:1.05}
.rpt-brief-stat .label{font-size:12px;color:var(--muted) !important;font-weight:750;margin-top:3px}
.rpt-direction{
  display:inline-flex;
  align-items:center;
  gap:8px;
  background:rgba(79,209,197,.11);
  border:1px solid rgba(79,209,197,.38);
  color:#b7fff5 !important;
  border-radius:999px;
  padding:8px 14px;
  font-weight:900;
  font-size:14px;
  margin-top:8px;
}
.rpt-today-advice{
  background:rgba(96,165,250,.10);
  border:1px solid rgba(96,165,250,.22);
  border-radius:14px;
  padding:13px 16px;
  margin-top:15px;
  font-size:13px;
  line-height:1.75;
  color:var(--ink-2) !important;
}
.rpt-today-advice b{color:var(--ink) !important}

/* ====== AGENT TIMELINE ====== */
.rpt-timeline{
  background:var(--panel);
  border:1px solid var(--line);
  border-radius:18px;
  padding:16px 18px;
  box-shadow:var(--card-shadow);
}
.rpt-timeline-row{display:flex;gap:6px;flex-wrap:wrap}
.rpt-tl-step{
  padding:6px 11px;
  border-radius:999px;
  font-size:11px;
  font-weight:850;
  background:rgba(255,255,255,.045);
  color:var(--muted) !important;
  border:1px solid var(--line);
}
.rpt-tl-done{
  background:rgba(52,211,153,.13);
  border-color:rgba(52,211,153,.36);
  color:#b7f7d7 !important;
}

/* ====== PORTFOLIO ====== */
.rpt-portfolio{display:flex;gap:16px;flex-wrap:wrap}
.rpt-portfolio-col{
  flex:1;
  min-width:235px;
  background:linear-gradient(180deg,var(--panel),#111923);
  border:1px solid var(--line);
  border-radius:18px;
  padding:16px 18px;
  box-shadow:var(--card-shadow);
}
.rpt-portfolio-col h3{font-size:15px;font-weight:950;margin:0 0 13px;color:var(--ink) !important}
.rpt-portfolio-col.safe{border-top:4px solid var(--green)}
.rpt-portfolio-col.safe h3{color:#b7f7d7 !important}
.rpt-portfolio-col.stretch{border-top:4px solid var(--orange)}
.rpt-portfolio-col.stretch h3{color:#fde68a !important}
.rpt-portfolio-col.hold{border-top:4px solid var(--red)}
.rpt-portfolio-col.hold h3{color:#fecdd3 !important}
.rpt-pf-item{
  padding:10px 11px;
  border-radius:12px;
  margin-bottom:8px;
  font-size:13px;
  line-height:1.55;
  cursor:default;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.06);
}
.rpt-pf-item:hover{background:rgba(79,209,197,.08);border-color:rgba(79,209,197,.25)}
.rpt-pf-item .title{font-weight:850;color:var(--ink) !important}
.rpt-pf-item .company{color:var(--muted) !important;font-size:12px;margin-top:2px}
.rpt-pf-item .reason{font-size:11px;color:var(--muted) !important;margin-top:4px}

/* ====== EVIDENCE BOARD ====== */
.rpt-jd-card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:12px;box-shadow:var(--card-shadow)}
.rpt-jd-card:hover{border-color:rgba(79,209,197,.4)}
.rpt-jd-header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;cursor:pointer}
.rpt-jd-header .left{flex:1}
.rpt-jd-header .score{font-size:28px;font-weight:950;text-align:center;min-width:64px;color:var(--cyan) !important}
.rpt-jd-body{display:none;margin-top:14px;padding-top:14px;border-top:1px solid var(--line)}
.rpt-jd-body.open{display:block}
.rpt-ev-block{margin-bottom:14px}
.rpt-ev-block h5{font-size:13px;font-weight:900;color:var(--ink) !important;margin-bottom:6px}
.rpt-ev-source{
  font-size:12px;
  color:var(--ink-2) !important;
  background:rgba(255,255,255,.045);
  border:1px solid var(--line);
  border-radius:12px;
  padding:10px 12px;
  line-height:1.7;
}
.rpt-ev-source b{color:var(--ink) !important}
.rpt-ev-item{
  font-size:12px;
  padding:7px 10px;
  border-radius:9px;
  margin:4px 0;
  border:1px solid transparent;
}
.rpt-ev-hit{background:rgba(52,211,153,.12);color:#c6f6dc !important;border-color:rgba(52,211,153,.28)}
.rpt-ev-gap{background:rgba(251,191,36,.13);color:#fde68a !important;border-color:rgba(251,191,36,.28)}
.rpt-ev-action{background:rgba(96,165,250,.13);color:#bfdbfe !important;border-color:rgba(96,165,250,.28)}
.rpt-ev-action-need-exp{background:rgba(251,113,133,.13);color:#fecdd3 !important;border-color:rgba(251,113,133,.28)}
.rpt-ev-link{font-size:12px;color:#93c5fd !important}

/* ====== WHAT-IF ====== */
.rpt-whatif-item{
  background:linear-gradient(180deg,var(--panel),#111923);
  border:1px solid var(--line);
  border-radius:15px;
  padding:15px 16px;
  margin-bottom:10px;
  display:flex;
  align-items:center;
  gap:14px;
  box-shadow:0 10px 30px rgba(0,0,0,.18);
}
.rpt-whatif-item:hover{border-color:rgba(79,209,197,.4)}
.rpt-whatif-gain{font-size:28px;font-weight:950;color:#9ff3ca !important;min-width:76px;text-align:center}
.rpt-whatif-body{flex:1}
.rpt-whatif-body .action{font-weight:900;font-size:14px;color:var(--ink) !important}
.rpt-whatif-body .why{color:var(--muted) !important;font-size:12px;margin-top:3px}

/* ====== ACTION QUEUE ====== */
.rpt-action-card{
  background:var(--panel);
  border:1px solid var(--line);
  border-radius:13px;
  padding:12px 14px;
  margin-bottom:8px;
  display:flex;
  align-items:center;
  gap:12px;
  box-shadow:0 8px 22px rgba(0,0,0,.12);
  color:var(--ink-2) !important;
}
.rpt-action-badge{font-size:11px;font-weight:800;padding:4px 10px;border-radius:8px;white-space:nowrap}
.rpt-action-badge.rewrite{background:rgba(52,211,153,.16);color:#b7f7d7 !important;border:1px solid rgba(52,211,153,.28)}
.rpt-action-badge.need-exp{background:rgba(251,191,36,.16);color:#fde68a !important;border:1px solid rgba(251,191,36,.28)}
.rpt-action-badge.no-fake{background:rgba(251,113,133,.16);color:#fecdd3 !important;border:1px solid rgba(251,113,133,.28)}

/* ====== BUTTON ====== */
.stButton>button{
  border-radius:12px !important;
  font-weight:850 !important;
  min-height:44px;
  background:#17202d !important;
  color:var(--ink) !important;
  border:1px solid var(--line-strong) !important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#10b981,#0ea5e9) !important;
  border:0 !important;
  box-shadow:0 12px 28px rgba(14,165,233,.25) !important;
  color:#061116 !important;
}
.stButton>button[kind="primary"] p{color:#061116 !important}

/* ====== STREAMLIT EXPANDERS IN REPORT ====== */
div[data-testid="stExpander"] div[role="button"],
div[data-testid="stExpander"] summary{
  color:var(--ink) !important;
}
div[data-testid="stExpander"] [data-testid="stMarkdownContainer"]{
  color:var(--ink-2) !important;
}

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
