"""
streamlit_app.py — Frontier AI Radar
------------------------------------------
Pages:
  📊 Dashboard          — KPIs, top signals, category + cluster breakdown
  🔄 What Changed       — NEW / UPDATED findings for any completed run
  📈 Observability      — /metrics: agent timing, run history, distributions
  🏷️ Entity Dashboard   — entity trends vs prior run, heatmap, topic clusters
  🔭 SOTA Watch         — benchmark leaderboard movements (spec bonus UI)
  🔍 Findings Explorer  — filterable findings table with full detail view
  ⚙️  Sources            — CRUD + per-source history + last_seen_at
  📁 Run History        — runs with per-agent timing, category breakdown, PDF
  📅 Schedule           — scheduler config, LLM + email status
"""

from datetime import datetime
import pandas as pd
import requests
import streamlit as st

import os
# On Streamlit Cloud: set BACKEND_URL in app secrets
# Locally: defaults to localhost:8000
API_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="🛰 Frontier AI Radar",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.score-high { color: #059669; font-weight: bold; }
.score-mid  { color: #d97706; font-weight: bold; }
.score-low  { color: #6b7280; }
.status-ok   { color: #059669; }
.status-fail { color: #dc2626; }
.trend-up   { color: #059669; font-weight: bold; }
.trend-down { color: #dc2626; font-weight: bold; }
.trend-new  { color: #2563eb; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛰 Frontier AI Radar")
    st.caption("v4.1 — Daily Intelligence System")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "📊 Dashboard",
            "🔄 What Changed",
            "📈 Observability",
            "🏷️ Entity Dashboard",
            "🔭 SOTA Watch",
            "🔍 Findings Explorer",
            "⚙️ Sources",
            "📁 Run History",
            "📅 Schedule",
        "📚 Digest Archive",
        "📧 Email Recipients",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    if st.button("🚀 Trigger Manual Run", type="primary", use_container_width=True):
        try:
            r = requests.post(f"{API_URL}/api/runs/trigger", timeout=5)
            if r.status_code == 200:
                st.success("✅ Run started! Refresh in ~60s.")
            elif r.status_code == 409:
                st.warning("⚠️ Run already in progress.")
                if st.button("🔧 Force Recover Stale Run", key="recover_btn"):
                    rec = requests.post(f"{API_URL}/api/runs/recover", timeout=5)
                    if rec.ok:
                        st.success(f"Recovered: {rec.json().get('message')}")
            else:
                st.error(f"Error {r.status_code}: {r.json().get('detail')}")
        except requests.ConnectionError:
            st.error("❌ API offline. Run: `uvicorn app.main:app --port 8000`")

    # Show recover button always if there might be stale runs
    with st.expander("🔧 Ops Tools"):
        if st.button("Recover Stale Runs", key="recover_ops"):
            try:
                rec = requests.post(f"{API_URL}/api/runs/recover", timeout=5)
                if rec.ok:
                    d = rec.json()
                    st.success(d.get("message", "Done"))
                else:
                    st.error(f"Failed: {rec.status_code}")
            except Exception as e:
                st.error(str(e))

    st.markdown("---")
    try:
        h = requests.get(f"{API_URL}/health", timeout=3)
        if h.ok:
            v = h.json().get("version", "")
            st.markdown(f'<span class="status-ok">● API Online {v}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-fail">● API Degraded</span>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<span class="status-fail">● API Offline</span>', unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────
def api_get(path: str, params: dict = None):
    _list_paths = ["findings", "runs", "sources", "entities", "snapshots", "clusters", "changes"]
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        # Pipeline running — API temporarily busy. Never show red error for this.
        if "status" in path or "runs" in path:
            st.info("⏳ Pipeline running — dashboard will refresh automatically. (~60–90s)")
        return [] if any(x in path for x in _list_paths) else {}
    except requests.ConnectionError:
        st.error("❌ Cannot connect to API (localhost:8000). Is uvicorn running?")
        st.stop()
    except Exception as e:
        # Swallow timeout-related errors silently during pipeline execution
        if "timed out" in str(e).lower() or "timeout" in str(e).lower():
            st.info("⏳ Pipeline running — results will appear once complete.")
            return [] if any(x in path for x in _list_paths) else {}
        st.error(f"API error on {path}: {e}")
        return [] if any(x in path for x in _list_paths) else {}

CATEGORY_ICONS  = {"competitors":"🏢","model_providers":"🤖","research":"📄","hf_benchmarks":"📊"}
CATEGORY_LABELS = {
    "competitors":"Competitor Intelligence","model_providers":"Foundation Model Providers",
    "research":"Research Publications","hf_benchmarks":"HF Benchmarks",
}
CONFIDENCE_LABELS = {1.0:"Official Source",0.8:"Lab Blog / Docs",0.6:"Third-party Report"}


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("🛰 Frontier AI Radar")
    st.caption(f"Loaded {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    status   = api_get("/api/status")
    findings = api_get("/api/findings", {"limit": 100})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Findings", status.get("total_findings", 0))
    c2.metric("Total Runs",     status.get("total_runs", 0))
    c3.metric("Completed",      status.get("completed_runs", 0))
    c4.metric("Sources",        len(api_get("/api/sources")))
    c5.metric("Pipeline",       "🟢 Running" if status.get("is_running") else "⚪ Idle")

    st.markdown("---")

    if not findings:
        st.info("No intelligence signals yet. Click **🚀 Trigger Manual Run** to start.")
        st.stop()

    st.subheader("🏆 Top Intelligence Signals")
    for i, f in enumerate(findings[:5], 1):
        score  = f.get("final_score", 0) or 0
        change = f.get("change_status", "new")
        badge  = "🆕" if change == "new" else "🔄"
        conf   = f.get("confidence_score", 0.8) or 0.8
        with st.expander(f"{badge} **[{score:.1f}]** {f.get('title','')} — {f.get('publisher','')}", expanded=(i==1)):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f.get("summary", ""))
                if f.get("why_matters"):
                    st.info(f"💡 {f['why_matters']}")
                if f.get("evidence"):
                    st.success(f"📎 **Evidence:** {f['evidence']}")
            with col2:
                st.metric("Score", f"{score:.1f}/10")
                st.metric("Confidence", f"{conf:.0%}")
                st.caption(f"🏷️ {f.get('topic_cluster','general')}")
                st.caption(f"{CATEGORY_ICONS.get(f.get('category',''),'📌')} {CATEGORY_LABELS.get(f.get('category',''),'')}")
                if f.get("source_url"):
                    st.markdown(f"[🔗 Source]({f['source_url']})")

    st.markdown("---")
    ca, cb = st.columns(2)
    with ca:
        st.subheader("📂 By Category")
        cats = {}
        for f in findings:
            k = CATEGORY_LABELS.get(f.get("category",""), f.get("category",""))
            cats[k] = cats.get(k, 0) + 1
        if cats:
            st.bar_chart(pd.DataFrame(list(cats.items()), columns=["Category","Count"]).set_index("Category"))
    with cb:
        st.subheader("🗂️ By Topic Cluster")
        clusters = {}
        for f in findings:
            k = f.get("topic_cluster") or "general"
            clusters[k] = clusters.get(k, 0) + 1
        if clusters:
            st.bar_chart(pd.DataFrame(list(clusters.items()), columns=["Cluster","Count"]).set_index("Cluster"))

    st.markdown("---")
    st.caption(f"Next scheduled run: {status.get('next_scheduled','N/A')} · API v{status.get('version','')}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WHAT CHANGED
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔄 What Changed":
    st.title("🔄 What Changed Since Last Run")

    runs      = api_get("/api/runs", {"limit": 10})
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    run_options  = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]} · {r.get('total_found',0)} signals": r["run_id"] for r in completed}
    selected_run = run_options[st.selectbox("Select Run", list(run_options.keys()))]
    changes      = api_get(f"/api/changes/{selected_run}")

    new_items     = changes.get("new", [])
    updated_items = changes.get("updated", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("🆕 New Signals",     len(new_items))
    c2.metric("🔄 Updated Signals", len(updated_items))
    c3.metric("⏸ Unchanged",        changes.get("unchanged", 0))

    st.markdown("---")
    if new_items:
        st.subheader(f"🆕 New Signals ({len(new_items)})")
        for f in new_items:
            score = f.get("final_score", 0) or 0
            conf  = f.get("confidence_score", 0.8) or 0.8
            with st.expander(f"[{score:.1f}] {f.get('title','')}"):
                c1, c2 = st.columns([3,1])
                with c1:
                    st.write(f.get("summary",""))
                    if f.get("why_matters"):
                        st.info(f"💡 {f['why_matters']}")
                    if f.get("evidence"):
                        st.success("📎 **Evidence:** " + f["evidence"])
                with c2:
                    st.metric("Confidence", f"{conf:.0%}")
                    st.caption(f"🏷️ {f.get('topic_cluster','general')}")
                    st.caption(f"📡 {f.get('publisher','')}")
                    if f.get("source_url"):
                        st.markdown(f"[🔗]({f['source_url']})")

    if updated_items:
        st.subheader(f"🔄 Updated Signals ({len(updated_items)})")
        for f in updated_items:
            score = f.get("final_score", 0) or 0
            with st.expander(f"[{score:.1f}] {f.get('title','')} *(updated)*"):
                st.write(f.get("summary",""))
                if f.get("why_matters"):
                    st.info(f"💡 {f['why_matters']}")
                if f.get("evidence"):
                    st.success("📎 **Evidence:** " + f["evidence"])
                if f.get("previous_hash"):
                    st.caption(f"Hash change: `{f['previous_hash'][:16]}...` → `{f.get('content_hash','')[:16] if f.get('content_hash') else 'N/A'}...`")

    if not new_items and not updated_items:
        st.success("✅ No changes detected — all sources unchanged since last run.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OBSERVABILITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Observability":
    st.title("📈 Observability Dashboard")
    st.caption("Agent performance, run history, signal distributions")

    metrics = api_get("/metrics")
    if not metrics or metrics.get("total_runs", 0) == 0:
        st.info("No completed runs yet.")
        st.stop()

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total Runs",      metrics.get("total_runs",0))
    k2.metric("Completed",       metrics.get("completed_runs",0))
    k3.metric("Failed",          metrics.get("failed_runs",0))
    k4.metric("Total Findings",  metrics.get("total_findings",0))
    k5.metric("Avg Elapsed (s)", metrics.get("avg_elapsed_sec",0))
    k6.metric("Avg Finds/Run",   metrics.get("avg_findings_per_run",0))

    st.markdown("---")

    runs_over_time = metrics.get("runs_over_time",[])
    if runs_over_time:
        st.subheader("📅 Findings Per Run")
        df = pd.DataFrame(runs_over_time)
        st.bar_chart(df.set_index("date")["count"])

    st.markdown("---")
    cl, cr = st.columns(2)

    with cl:
        st.subheader("🤖 Per-Agent Performance")
        agents = metrics.get("agent_metrics",[])
        if agents:
            st.dataframe(
                pd.DataFrame(agents).rename(columns={
                    "name":"Agent","total_found":"Total Findings",
                    "success_runs":"OK Runs","error_runs":"Error Runs","avg_elapsed":"Avg Elapsed (s)"
                }),
                use_container_width=True, hide_index=True,
            )

    with cr:
        st.subheader("🔄 Change Detection Summary")
        cs = metrics.get("change_stats",{})
        if cs:
            st.bar_chart(pd.DataFrame(list(cs.items()), columns=["Status","Count"]).set_index("Status"))

    st.markdown("---")
    ca, cb = st.columns(2)
    with ca:
        st.subheader("📂 By Category")
        cd = metrics.get("findings_by_category",{})
        if cd:
            st.bar_chart(pd.DataFrame(list(cd.items()), columns=["Category","Count"]).set_index("Category"))
    with cb:
        st.subheader("🗂️ By Cluster")
        cl2 = metrics.get("findings_by_cluster",{})
        if cl2:
            st.bar_chart(pd.DataFrame(list(cl2.items()), columns=["Cluster","Count"]).set_index("Cluster"))

    st.markdown("---")
    st.subheader("🏢 Top Entities (All Time)")
    te = metrics.get("top_entities",[])
    if te:
        st.bar_chart(pd.DataFrame(te[:15]).set_index("entity")["count"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ENTITY DASHBOARD (v4.1: entity trends vs prior run)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏷️ Entity Dashboard":
    st.title("🏷️ Entity Dashboard")
    st.caption("Entity mention trends vs prior run — which companies and models gained/lost mindshare")

    runs      = api_get("/api/runs", {"limit": 10})
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    run_options  = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    selected_run = run_options[st.selectbox("Select Run", list(run_options.keys()))]

    # Entity trends vs prior run
    trends_data = api_get(f"/api/entity-trends/{selected_run}")
    trends      = trends_data.get("entity_trends", {})

    if trends:
        st.subheader("📈 Entity Mention Trends vs Prior Run")

        trend_rows = []
        for entity, info in trends.items():
            trend = info.get("trend","stable")
            trend_icon = {"up":"⬆️","down":"⬇️","new":"🆕","stable":"➡️"}.get(trend,"")
            trend_rows.append({
                "Entity":   entity.title(),
                "Trend":    f"{trend_icon} {trend}",
                "Current":  info.get("current",0),
                "Previous": info.get("previous",0),
                "Delta":    info.get("delta",0),
            })
        trend_rows.sort(key=lambda x: abs(x["Delta"]), reverse=True)

        df_trends = pd.DataFrame(trend_rows)
        st.dataframe(df_trends, use_container_width=True, hide_index=True)

        st.markdown("---")
        # Highlight risers and fallers
        risers  = [r for r in trend_rows if r["Delta"] > 0]
        fallers = [r for r in trend_rows if r["Delta"] < 0]
        new_ent = [r for r in trend_rows if "🆕" in r["Trend"]]

        t1, t2, t3 = st.columns(3)
        with t1:
            st.markdown("**⬆️ Rising Entities**")
            for r in risers[:5]:
                st.markdown(f'<span class="trend-up">+{r["Delta"]} {r["Entity"]}</span>', unsafe_allow_html=True)
        with t2:
            st.markdown("**⬇️ Falling Entities**")
            for r in fallers[:5]:
                st.markdown(f'<span class="trend-down">{r["Delta"]} {r["Entity"]}</span>', unsafe_allow_html=True)
        with t3:
            st.markdown("**🆕 New This Run**")
            for r in new_ent[:5]:
                st.markdown(f'<span class="trend-new">{r["Entity"]}</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Standard entity counts
    col1, col2 = st.columns([2,1])
    scope = col1.radio("Scope", ["All Time","Latest Run"], horizontal=True)
    top_n = col2.selectbox("Show top", [10,20,30], index=1)

    params = {"limit": top_n}
    if scope == "Latest Run":
        params["run_id"] = selected_run

    entities = api_get("/api/entities", params)
    if entities:
        df = pd.DataFrame(entities)
        st.subheader(f"Top {len(df)} Entities")
        st.bar_chart(df.set_index("entity")["count"])

    st.markdown("---")
    st.subheader("🗂️ Topic Clusters")
    clusters = api_get("/api/clusters", {"run_id": selected_run})
    if clusters:
        cluster_cols = st.columns(min(3, len(clusters)))
        for i, (name, items) in enumerate(clusters.items()):
            col = cluster_cols[i % 3]
            col.markdown(f"**{name.title()}** ({len(items)})")
            for item in items[:4]:
                score = item.get("final_score",0) or 0
                badge = "🆕" if item.get("change_status")=="new" else "🔄"
                col.caption(f"{badge} [{score:.1f}] {item.get('title','')[:45]}...")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SOTA WATCH (v4.1 NEW — spec bonus UI)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔭 SOTA Watch":
    st.title("🔭 SOTA Watch")
    st.caption("Benchmark leaderboard movements detected between runs — who moved up or down")

    runs      = api_get("/api/runs", {"limit": 10})
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        st.info("No completed runs yet.")
        st.stop()

    run_options  = {f"Run {r['run_id'][:8]} · {str(r.get('started_at',''))[:16]}": r["run_id"] for r in completed}
    selected_run = run_options[st.selectbox("Select Run", list(run_options.keys()))]

    sota = api_get(f"/api/sota-watch/{selected_run}")
    events = sota.get("sota_watch",[])

    if not events:
        st.info(
            "No benchmark leaderboard movements detected for this run. "
            "SOTA Watch activates when HF Benchmark findings appear across multiple runs "
            "with different impact scores."
        )
        st.markdown("---")
        st.subheader("📊 HF Benchmark Findings This Run")
        hf_findings = api_get("/api/findings", {"category":"hf_benchmarks","limit":20})
        if hf_findings:
            for f in hf_findings:
                score = f.get("final_score",0) or 0
                with st.expander(f"[{score:.1f}] {f.get('title','')}"):
                    st.write(f.get("summary",""))
                    if f.get("evidence"):
                        st.success("📎 " + f["evidence"])
                    st.caption(f"Source: {f.get('source_url','')}")
        else:
            st.info("No HF Benchmark findings yet.")
    else:
        st.subheader(f"📊 {len(events)} Leaderboard Movement(s) Detected")
        for event in events:
            delta    = event.get("delta",0)
            movement = event.get("movement","")
            icon     = "⬆️" if movement == "up" else "⬇️"
            color    = "trend-up" if movement == "up" else "trend-down"
            with st.expander(f"{icon} {event.get('title','')} ({'+' if delta>0 else ''}{delta:.1f} impact points)"):
                c1, c2 = st.columns(2)
                c1.metric("Current Impact Score", f"{event.get('current_score',0):.1f}")
                c2.metric("Previous Impact Score", f"{event.get('previous_score',0):.1f}", delta=f"{delta:.1f}")
                st.caption(f"Source: {event.get('source_url','')}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FINDINGS EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Findings Explorer":
    st.title("🔍 Findings Explorer")

    fc1,fc2,fc3,fc4 = st.columns([2,3,2,1])
    cat_filter = fc1.selectbox(
        "Category",
        ["All","competitors","model_providers","research","hf_benchmarks"],
        format_func=lambda x: CATEGORY_LABELS.get(x,x) if x!="All" else "All Categories",
    )
    search         = fc2.text_input("Search", placeholder="e.g. GPT-5, benchmark, pricing...")
    cluster_filter = fc3.selectbox(
        "Topic Cluster",
        ["All","model releases","benchmarks & evals","safety & alignment",
         "agents & reasoning","multimodal","infrastructure","research","open source","general"],
    )
    limit = fc4.selectbox("Show", [25,50,100,200], index=1)

    params: dict = {"limit": limit}
    if cat_filter != "All":
        params["category"] = cat_filter
    if search:
        params["search"] = search
    if cluster_filter != "All":
        params["cluster"] = cluster_filter

    findings = api_get("/api/findings", params)
    st.caption(f"{len(findings)} findings")

    if findings:
        df = pd.DataFrame([{
            "Score":     f.get("final_score",0),
            "Conf":      f"{(f.get('confidence_score',0.8) or 0.8):.0%}",
            "Status":    f.get("change_status","new"),
            "Title":     f.get("title","")[:80],
            "Category":  CATEGORY_LABELS.get(f.get("category",""),f.get("category","")),
            "Cluster":   f.get("topic_cluster","general"),
            "Publisher": f.get("publisher","—"),
            "Tags":      ", ".join((f.get("tags") or [])[:3]),
            "URL":       f.get("source_url",""),
        } for f in findings])

        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.2f", width="small"),
                "URL":   st.column_config.LinkColumn("Source", width="medium"),
                "Title": st.column_config.TextColumn("Title", width="large"),
            },
        )

        st.markdown("---")
        st.subheader("📄 Finding Detail")
        titles   = [f.get("title","")[:80] for f in findings]
        selected = st.selectbox("📌 Select finding", titles)
        if selected:
            finding = next((f for f in findings if f.get("title","").startswith(selected[:30])), None)
            if finding:
                c1, c2 = st.columns([3,1])
                c1.markdown(f"### {finding.get('title')}")
                score  = finding.get("final_score",0) or 0
                conf   = finding.get("confidence_score",0.8) or 0.8
                change = finding.get("change_status","new")
                c2.metric("Score", f"{score:.1f}/10")
                c2.metric("Confidence", f"{conf:.0%}")
                c2.caption({"new":"🆕 New","updated":"🔄 Updated","unchanged":"⏸ Unchanged"}.get(change,change))
                c2.caption(CONFIDENCE_LABELS.get(conf,""))

                st.write(finding.get("summary",""))
                if finding.get("why_matters"):
                    st.info(f"💡 {finding['why_matters']}")
                if finding.get("evidence"):
                    st.success("📎 **Evidence (verbatim):** " + finding["evidence"])

                ca2, cb2 = st.columns(2)
                ca2.write(f"**Publisher:** {finding.get('publisher','—')}")
                ca2.write(f"**Cluster:** {finding.get('topic_cluster','general')}")
                cb2.markdown(f"**Source:** [{finding.get('source_url','')[:50]}]({finding.get('source_url','')})")
                if finding.get("previous_hash"):
                    cb2.caption(f"Prev hash: `{finding['previous_hash'][:16]}...`")
                if finding.get("tags"):
                    st.write("**Tags:** " + " ".join(f"`{t}`" for t in finding["tags"]))
                if finding.get("entities"):
                    st.write("**Entities:** " + " · ".join(f"**{e}**" for e in finding["entities"]))
    else:
        st.info("No findings match your filters.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SOURCES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Sources":
    st.title("⚙️ Source Management")

    with st.form("add_source", clear_on_submit=True):
        st.subheader("➕ Add New Source")
        c1,c2,c3 = st.columns([2,4,2])
        name       = c1.text_input("Name *", placeholder="OpenAI Blog")
        url        = c2.text_input("URL *", placeholder="https://openai.com/blog")
        agent_type = c3.selectbox("Agent Type *",
            ["competitors","model_providers","research","hf_benchmarks"],
            format_func=lambda x: CATEGORY_LABELS.get(x,x))
        if st.form_submit_button("Add Source", type="primary"):
            if not name.strip():
                st.error("Name required")
            elif not url.strip().startswith("http"):
                st.error("URL must start with http://")
            else:
                try:
                    r = requests.post(f"{API_URL}/api/sources",
                        json={"name":name.strip(),"url":url.strip(),"agent_type":agent_type},timeout=5)
                    if r.ok:
                        st.success(f"✅ Added: {name}")
                        st.rerun()
                    elif r.status_code == 400:
                        st.warning("⚠️ URL already exists.")
                    else:
                        st.error(f"Failed: {r.text}")
                except Exception as e:
                    st.error(str(e))

    st.markdown("---")
    st.subheader("Active Sources")
    sources = api_get("/api/sources")
    if sources:
        for src in sources:
            c1,c2,c3,c4,c5,c6 = st.columns([2,4,2,2,1,1])
            c1.write(f"**{src.get('name','')}**")
            c2.write(f"`{src.get('url','')}`")
            c3.write(f"_{CATEGORY_LABELS.get(src.get('agent_type',''),src.get('agent_type',''))}_")
            ls = src.get("last_seen_at")
            c4.caption(f"Last seen: {str(ls)[:16] if ls else 'Never'}")
            c5.write(f"#{src['id']}")
            if c6.button("🗑", key=f"del_{src['id']}"):
                try:
                    r = requests.delete(f"{API_URL}/api/sources/{src['id']}", timeout=5)
                    if r.ok:
                        st.success(f"Removed {src.get('name')}")
                        st.rerun()
                except Exception as e:
                    st.error(str(e))
    else:
        st.info("No sources yet. Add one above or trigger a run to auto-seed from config.yaml.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RUN HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Run History":
    st.title("📁 Run History")
    runs = api_get("/api/runs")
    if not runs:
        st.info("No runs yet. Click 🚀 Trigger Manual Run.")
        st.stop()

    icons = {"completed":"✅","failed":"❌","running":"⏳"}
    for run in runs:
        status   = run.get("status","unknown")
        run_id   = run.get("run_id","")
        found    = run.get("total_found",0)
        elapsed  = run.get("elapsed_sec")
        label    = f"{icons.get(status,'❓')} Run {run_id[:8]}... · {str(run.get('started_at',''))[:16]} · {status.upper()} · {found} signals"
        if elapsed:
            label += f" · {elapsed}s"

        with st.expander(label, expanded=(status=="running")):
            r1,r2,r3 = st.columns(3)
            r1.write(f"**Run ID:** `{run_id}`")
            r1.write(f"**Status:** {status}")
            r2.write(f"**Started:** {str(run.get('started_at',''))[:19]}")
            r2.write(f"**Finished:** {str(run.get('finished_at',''))[:19] or 'In progress'}")
            r3.write(f"**Signals:** {found}")
            if elapsed:
                r3.write(f"**Elapsed:** {elapsed}s")

            # Category breakdown
            fbc = run.get("findings_by_category",{})
            if fbc:
                st.markdown("**By Category:**")
                cat_cols = st.columns(len(fbc))
                for i,(cat,count) in enumerate(fbc.items()):
                    cat_cols[i].metric(f"{CATEGORY_ICONS.get(cat,'📌')} {cat}",count)

            # Agent breakdown
            ast = run.get("agent_status",{})
            if ast:
                st.markdown("**Per-Agent Results:**")
                agent_cols = st.columns(len(ast))
                for i,(name,info) in enumerate(ast.items()):
                    ic    = "✅" if info.get("status")=="ok" else ("⏱️" if info.get("status")=="timeout" else "❌")
                    label2 = f"{info.get('found',0)} signals"
                    if info.get("elapsed_sec"):
                        label2 += f" · {info['elapsed_sec']}s"
                    agent_cols[i].metric(f"{ic} {name}", label2)

            if run.get("pdf_path"):
                col_dl1, col_dl2 = st.columns(2)
                col_dl1.markdown(f"[📥 Open PDF]({API_URL}/api/digest/{run_id}/pdf)")
                try:
                    import os as _os
                    pdf_local = run["pdf_path"]
                    for base in ["backend", ".", ""]:
                        pdf_abs = _os.path.join(base, pdf_local) if base else pdf_local
                        if _os.path.exists(pdf_abs):
                            with open(pdf_abs, "rb") as _fh:
                                col_dl2.download_button(
                                    "⬇️ Save PDF",
                                    _fh.read(),
                                    file_name=f"radar_{run_id[:8]}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_{run_id}",
                                )
                            break
                except Exception:
                    pass

            if status=="failed" and run.get("error_log"):
                with st.expander("❌ Error Details"):
                    st.code(run["error_log"], language="text")

            if st.button("📋 View Top Findings", key=f"view_{run_id}"):
                ff = api_get(f"/api/findings/{run_id}")
                for f in ff[:8]:
                    score  = f.get("final_score",0)
                    change = "🆕" if f.get("change_status")=="new" else "🔄"
                    st.write(f"• {change} [{score:.1f}] **{f.get('title','')}**")
                    st.caption(f"  {f.get('summary','')[:100]}...")

            if status=="running":
                if st.button("🔄 Refresh", key=f"ref_{run_id}"):
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📚 Digest Archive":
    st.title("📚 Digest Archive")
    st.caption("All past PDF digests — browse, search, and download")

    runs = api_get("/api/runs")
    completed = [r for r in runs if r.get("status") == "completed" and r.get("pdf_path")]

    if not completed:
        st.info("No completed runs with digests yet.")
        st.stop()

    # Search
    search = st.text_input("🔍 Search by date or run ID", placeholder="2026-03-05 or b6d68b8f")
    if search:
        completed = [r for r in completed if
                     search.lower() in str(r.get("started_at","")).lower() or
                     search.lower() in r.get("run_id","").lower()]

    st.markdown(f"**{len(completed)} digest(s) found**")
    st.markdown("---")

    for run in completed:
        run_id  = run.get("run_id","")
        started = str(run.get("started_at",""))[:16]
        found   = run.get("total_found", 0)
        elapsed = run.get("elapsed_sec","")
        fbc     = run.get("findings_by_category", {})

        with st.expander(f"📄 Digest — {started}  ·  {found} signals", expanded=False):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**Run ID:** `{run_id[:8]}...`")
            c1.write(f"**Date:** {started}")
            c2.write(f"**Signals:** {found}")
            if elapsed:
                c2.write(f"**Elapsed:** {elapsed}s")

            # Category breakdown
            if fbc:
                cat_str = "  ·  ".join(f"{CATEGORY_ICONS.get(k,'📌')} {k}: {v}" for k,v in fbc.items())
                st.caption(cat_str)

            # Download buttons
            dl1, dl2 = st.columns(2)
            dl1.markdown(f"[📥 Open PDF in browser]({API_URL}/api/digest/{run_id}/pdf)")
            try:
                import os as _os
                pdf_local = run["pdf_path"]
                for base in ["backend", ".", ""]:
                    pdf_abs = _os.path.join(base, pdf_local) if base else pdf_local
                    if _os.path.exists(pdf_abs):
                        with open(pdf_abs, "rb") as _fh:
                            dl2.download_button(
                                "⬇️ Save PDF",
                                _fh.read(),
                                file_name=f"radar_digest_{started[:10]}.pdf",
                                mime="application/pdf",
                                key=f"arch_{run_id}",
                            )
                        break
            except Exception:
                pass

            # Quick findings preview
            if st.button(f"👁 Preview top findings", key=f"prev_{run_id}"):
                findings = api_get(f"/api/findings/{run_id}")
                if findings:
                    for f in findings[:5]:
                        score = f.get("final_score", 0) or 0
                        st.write(f"**[{score:.1f}]** {f.get('title','')}")
                        st.caption(f.get("summary","")[:120] + "...")
                else:
                    st.caption("No findings for this run.")


elif page == "📧 Email Recipients":
    st.title("📧 Email Recipients")
    st.caption("Manage who receives the daily AI Radar digest — spec FR6")

    # ── Resend info banner ────────────────────────────────────────────────
    st.info(
        "📬 **No DNS verification needed.**  "
        "Frontier AI Radar uses Resend's shared domain (`onboarding@resend.dev`).  "
        "Just add your `RESEND_API_KEY` to `.env` — emails work immediately on any network."
    )

    # ── Current recipients ────────────────────────────────────────────────
    st.subheader("📋 Current Recipients")
    recipients = api_get("/api/email-recipients") or []

    if not recipients:
        st.warning("No recipients configured yet. Add one below.")
    else:
        active   = [r for r in recipients if r.get("is_active", 1)]
        inactive = [r for r in recipients if not r.get("is_active", 1)]
        st.caption(f"{len(active)} active · {len(inactive)} paused · {len(recipients)} total")

        for rec in recipients:
            rid      = rec.get("id")
            email    = rec.get("email", "")
            name     = rec.get("name") or ""
            note     = rec.get("note") or ""
            active   = rec.get("is_active", 1)
            status   = "✅ Active" if active else "⏸ Paused"
            label    = f"{status}  ·  **{email}**" + (f"  ·  {name}" if name else "")

            with st.expander(label, expanded=False):
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(f"**Email:** {email}")
                c2.write(f"**Name:** {name or '—'}")
                if note:
                    st.caption(f"Note: {note}")

                # Toggle active
                toggle_label = "⏸ Pause" if active else "▶️ Activate"
                if c3.button(toggle_label, key=f"tog_{rid}"):
                    try:
                        r = requests.patch(f"{API_URL}/api/email-recipients/{rid}/toggle", timeout=5)
                        if r.status_code == 200:
                            st.success(f"{'Paused' if active else 'Activated'}: {email}")
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Failed"))
                    except Exception as e:
                        st.error(str(e))

                # Delete
                if c4.button("🗑 Remove", key=f"del_{rid}"):
                    try:
                        r = requests.delete(f"{API_URL}/api/email-recipients/{rid}", timeout=5)
                        if r.status_code == 200:
                            st.success(f"Removed: {email}")
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Failed"))
                    except Exception as e:
                        st.error(str(e))

    st.markdown("---")

    # ── Add new recipient ─────────────────────────────────────────────────
    st.subheader("➕ Add Recipient")
    with st.container():
        a1, a2, a3 = st.columns([3, 2, 2])
        new_email = a1.text_input("Email address *", placeholder="researcher@company.com", key="new_email")
        new_name  = a2.text_input("Name (optional)", placeholder="Dr. Smith", key="new_name")
        new_note  = a3.text_input("Note (optional)", placeholder="Research team lead", key="new_note")

        if st.button("➕ Add to List", type="primary"):
            if not new_email or "@" not in new_email:
                st.error("Please enter a valid email address.")
            else:
                try:
                    r = requests.post(
                        f"{API_URL}/api/email-recipients",
                        json={"email": new_email, "name": new_name or None, "note": new_note or None},
                        timeout=5,
                    )
                    if r.status_code == 200:
                        st.success(f"✅ Added: {new_email}")
                        st.rerun()
                    elif r.status_code == 409:
                        st.warning(f"{new_email} is already in the list.")
                    else:
                        st.error(r.json().get("detail", "Failed to add recipient"))
                except Exception as e:
                    st.error(str(e))

    st.markdown("---")

    # ── Send test email ───────────────────────────────────────────────────
    st.subheader("🧪 Send Test Email")
    st.caption("Verify your Resend integration is working — sends immediately, no pipeline run needed")

    t1, t2 = st.columns([4, 1])
    test_addr = t1.text_input("Send test to", placeholder="your-email@gmail.com", key="test_email")
    if t2.button("📤 Send Test", type="secondary"):
        if not test_addr or "@" not in test_addr:
            st.error("Enter a valid email address")
        else:
            with st.spinner("Sending..."):
                try:
                    r = requests.post(
                        f"{API_URL}/api/email-recipients/test",
                        json={"email": test_addr},
                        timeout=15,
                    )
                    if r.status_code == 200:
                        result = r.json()
                        st.success(f"✅ Test email sent to **{test_addr}** via {result.get('provider', 'Resend')}")
                        st.caption("Check your inbox (and spam folder) — arrives within 30 seconds.")
                    else:
                        detail = r.json().get("detail", "Unknown error")
                        st.error(f"❌ Failed: {detail}")
                        st.caption("Make sure RESEND_API_KEY is set in backend/.env")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    st.markdown("---")

    # ── How it works ─────────────────────────────────────────────────────
    with st.expander("ℹ️ How email delivery works"):
        st.markdown("""
**Provider:** Resend API (port 443 — works on all networks including corporate)

**No DNS setup required** — emails are sent from `onboarding@resend.dev` (Resend's pre-verified shared domain).
You only need to verify your own domain if you want to send from your own `@yourcompany.com` address.

**Priority:** Recipients added here (DB) take priority over `config.yaml` email_recipients.
If no recipients are in the DB, the system falls back to `config.yaml`.

**Get your free Resend API key:**
1. Go to [resend.com](https://resend.com) → Sign up with Google (30 seconds)
2. Dashboard → API Keys → Create key
3. Add to `backend/.env`:
```
RESEND_API_KEY=re_your_actual_key_here
```
4. Use the test button above to verify it works.

**Free tier:** 100 emails/day · 3,000 emails/month
        """)


elif page == "📅 Schedule":
    st.title("📅 Scheduler")
    status = api_get("/api/status")

    c1,c2 = st.columns(2)
    with c1:
        st.subheader("⏰ Next Scheduled Run")
        next_run = status.get("next_scheduled")
        if next_run:
            try:
                next_dt = datetime.fromisoformat(next_run)
                st.metric("Next Run", next_dt.strftime("%Y-%m-%d %H:%M %Z"))
                delta = next_dt.replace(tzinfo=None) - datetime.utcnow()
                h,m   = int(delta.total_seconds()//3600), int((delta.total_seconds()%3600)//60)
                st.caption(f"In approximately {h}h {m}m")
            except Exception:
                st.write(next_run)
        else:
            st.warning("Scheduler not running")
    with c2:
        st.subheader("📊 Stats")
        st.metric("Total Signals", status.get("total_findings",0))
        st.metric("Total Runs",    status.get("total_runs",0))
        st.metric("Completed",     status.get("completed_runs",0))

    st.markdown("---")
    st.subheader("⚙️ Config")
    st.info(
        "Edit **config.yaml** to change schedule:\n```yaml\nglobal:\n"
        "  run_time: '07:00'\n  timezone: 'UTC'\n```\nRestart API to apply."
    )

    st.subheader("🔑 Configuration Status")
    st.caption("Read from backend — accurate regardless of where keys are stored")

    # Read from /api/status — backend reads its own env, not the frontend's
    llm_status        = status.get("llm_status", "❌ Not configured")
    email_status      = status.get("email_status", "❌ Not configured")
    active_recipients = status.get("active_recipients", 0)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**🤖 LLM Provider**")
        st.write(llm_status)
        st.markdown("**📧 Email Provider**")
        st.write(email_status)
    with col_b:
        st.markdown("**👥 Active Email Recipients**")
        if active_recipients > 0:
            st.success(f"✅ {active_recipients} recipient(s) configured")
            st.caption("Manage in 📧 Email Recipients page")
        else:
            st.warning("⚠️ No recipients — add them in 📧 Email Recipients page")

    # Quick links
    st.markdown("---")
    st.subheader("🔗 Quick Links")
    q1, q2, q3 = st.columns(3)
    q1.markdown("[📡 API Docs](http://localhost:8000/docs)")
    q2.markdown("[🗄 DB Explorer](http://localhost:8000/admin/db)")
    q3.markdown("[📊 Metrics JSON](http://localhost:8000/metrics)")