"""Streamlit Dashboard for BusinessInsight AI - Multi-Agent Business Intelligence Analyst.

NOTE: This frontend communicates EXCLUSIVELY via HTTP REST API calls to the FastAPI backend.
No direct backend functions or databases are invoked.
"""

import os
from typing import Any, Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="BusinessInsight AI | Multi-Agent BI Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .badge-verified {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .api-badge {
        background-color: #EEF2FF;
        color: #3730A3;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: monospace;
    }
    </style>
""",
    unsafe_allow_html=True,
)


st.markdown('<div class="main-header">📈 BusinessInsight AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Multi-Agent Business Intelligence Analyst powered by <b>Microsoft Agent Framework</b> and <b>Google Gemini</b>.<br>'
    '<span class="api-badge">REST API Client Mode</span> Communicating strictly via FastAPI endpoints.</div>',
    unsafe_allow_html=True,
)


st.sidebar.title("🎛️ Analysis Controls")

DEFAULT_API_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
api_base_url = st.sidebar.text_input("FastAPI Endpoint URL", value=DEFAULT_API_URL).rstrip("/")


def call_api(
    method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Helper to dispatch HTTP requests to FastAPI backend."""
    url = f"{api_base_url}{endpoint}"
    try:
        if method.upper() == "GET":
            resp = requests.get(url, params=params, timeout=30)
        else:
            resp = requests.post(url, json=json_data, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.HTTPError as e:
        try:
            err_detail = resp.json().get("detail", str(e))
        except Exception:
            err_detail = str(e)
        st.error(f"API Error ({resp.status_code}) on `{endpoint}`: {err_detail}")
        return None
    except Exception as e:
        st.error(f"Unexpected connection error on `{endpoint}`: {e}")
        return None


health_data = call_api("GET", "/health")

if health_data is None:
    st.error(
        f"⚠️ **Cannot Connect to FastAPI Backend at `{api_base_url}`**\n\n"
        "The Streamlit dashboard requires the FastAPI backend service to be running.\n\n"
        "**To start the backend, run this command in your terminal:**\n"
        "```bash\n"
        "python -m uvicorn businessinsight.main:app --host 127.0.0.1 --port 8000\n"
        "```\n"
        "Once running, refresh this page."
    )
    st.stop()


if health_data.get("maf_gemini_ready"):
    st.sidebar.success("🤖 MAF & Gemini API: **Ready**")
else:
    st.sidebar.info("💡 MAF Gemini: API Key not set. Backend operating in **Deterministic Intelligence Mode**.")

if not health_data.get("dataset_exists"):
    st.error("⚠️ **Demonstration Dataset Not Found on Backend**")
    st.markdown(
        """
        The sales dataset is missing from the configured backend path.

        ### How to set up the dataset manually:
        1. Download the real Kaggle Superstore dataset from:
           👉 [**Kaggle: Superstore Dataset by Vivek Singh**](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
        2. Extract the archive and place the CSV at:
           `data/raw/superstore.csv`
        3. Refresh this page to reload the application.
        """
    )
    st.stop()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_profile() -> Optional[Dict[str, Any]]:
    return call_api("GET", "/dataset/profile")


profile_data = fetch_profile() or {}


@st.cache_data(ttl=60, show_spinner="Querying FastAPI baseline analytics...")
def fetch_analytics(
    category: Optional[str] = None,
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    comparison_mode: str = "latest_vs_previous_quarter",
) -> Optional[Dict[str, Any]]:
    params: Dict[str, Any] = {"comparison_mode": comparison_mode}
    if category and category != "All Categories":
        params["category"] = category
    if region and region != "All Regions":
        params["region"] = region
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return call_api("GET", "/dataset/analytics", params=params)


initial_analytics = fetch_analytics() or {}
avail_cats = ["All Categories"] + initial_analytics.get("available_categories", [])
avail_regs = ["All Regions"] + initial_analytics.get("available_regions", [])

st.sidebar.markdown("---")
st.sidebar.subheader("Dataset Slice Filters")

selected_category = st.sidebar.selectbox("Product Category", avail_cats)
selected_region = st.sidebar.selectbox("Geographic Region", avail_regs)

min_date_str = initial_analytics.get("min_date")
max_date_str = initial_analytics.get("max_date")

selected_start_date = None
selected_end_date = None

if min_date_str and max_date_str:
    min_date = pd.to_datetime(min_date_str).date()
    max_date = pd.to_datetime(max_date_str).date()
    date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        selected_start_date = date_range[0].strftime("%Y-%m-%d")
        selected_end_date = date_range[1].strftime("%Y-%m-%d")


analytics_data = fetch_analytics(
    category=selected_category,
    region=selected_region,
    start_date=selected_start_date,
    end_date=selected_end_date,
)

if not analytics_data:
    st.warning("No analytics data returned from API for the selected filter criteria.")
    st.stop()

kpis = analytics_data.get("kpis", {})


tab_overview, tab_trends, tab_products, tab_regions, tab_ai, tab_reports = st.tabs(
    [
        "📊 KPI Overview",
        "📈 Trend Analysis",
        "📦 Product & Category",
        "🗺️ Regional Performance",
        "🤖 AI Multi-Agent Studio",
        "📄 Executive Reports",
    ]
)


with tab_overview:
    st.subheader("Key Performance Indicators")
    st.caption("Data source: `GET /dataset/analytics`")

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total Revenue", f"${kpis.get('total_sales', 0.0):,.2f}")
    with k2:
        st.metric("Distinct Orders", f"{kpis.get('distinct_orders', 0):,}")
    with k3:
        st.metric("Average Order Value", f"${kpis.get('average_order_value', 0.0):,.2f}")
    with k4:
        st.metric("Units Fulfilled", f"{kpis.get('total_units_sold', 0):,}")
    with k5:
        profit = kpis.get("total_profit")
        margin = kpis.get("profit_margin_pct")
        if profit is not None:
            st.metric("Net Profit", f"${profit:,.2f}", f"{margin or 0.0:.1f}% margin")
        else:
            st.metric("Net Profit", "N/A")

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("Monthly Sales Velocity")
        monthly_trend = analytics_data.get("monthly_trend", {})
        data_points = monthly_trend.get("data_points", [])
        if data_points:
            m_df = pd.DataFrame(data_points)
            fig_m = px.area(
                m_df,
                x="period",
                y="sales",
                labels={"period": "Month", "sales": "Revenue ($)"},
                color_discrete_sequence=["#2563EB"],
            )
            fig_m.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_m, use_container_width=True)

    with col_right:
        st.subheader("Data Hygiene & Governance")
        qs = profile_data.get("quality_summary", {})
        st.write(f"**Total Records:** {qs.get('total_rows', 0):,}")
        st.write(f"**Duplicate Rows:** {qs.get('duplicate_rows', 0):,}")
        st.write(f"**Database Used:** `None (In-Memory Processing)`")
        st.write(f"**API Health Status:** `{health_data.get('status', 'healthy').upper()}`")
        if qs.get("warnings"):
            with st.expander("Inspection Warnings", expanded=False):
                for w in qs["warnings"]:
                    st.warning(w)


with tab_trends:
    st.subheader("Temporal Trend & Period Comparisons")
    st.caption("Data source: `GET /dataset/analytics`")

    trend_view = st.radio("Aggregation Interval", ["Quarterly Trends", "Monthly Trends"], horizontal=True)

    if trend_view == "Quarterly Trends":
        q_res = analytics_data.get("quarterly_trend", {})
        q_points = q_res.get("data_points", [])
        if q_points:
            q_df = pd.DataFrame(q_points)
            fig_q = px.bar(
                q_df,
                x="period",
                y="sales",
                color="aov",
                labels={"sales": "Revenue ($)", "period": "Quarter", "aov": "AOV ($)"},
                title="Quarterly Sales Revenue with AOV Intensity",
                color_continuous_scale="Blues",
            )
            fig_q.update_layout(template="plotly_white")
            st.plotly_chart(fig_q, use_container_width=True)

            st.write("### Quarterly Data Table")
            st.dataframe(
                q_df[
                    [
                        "period",
                        "sales",
                        "orders",
                        "aov",
                        "profit",
                        "profit_margin_pct",
                        "percentage_sales_change",
                    ]
                ],
                use_container_width=True,
            )
    else:
        m_res = analytics_data.get("monthly_trend", {})
        m_points = m_res.get("data_points", [])
        if m_points:
            m_df = pd.DataFrame(m_points)
            fig_m = px.line(
                m_df,
                x="period",
                y="sales",
                markers=True,
                labels={"sales": "Revenue ($)", "period": "Month"},
                title="Monthly Revenue Trajectory",
            )
            fig_m.update_layout(template="plotly_white")
            st.plotly_chart(fig_m, use_container_width=True)


with tab_products:
    st.subheader("Product & Category Diagnostics")
    st.caption("Data source: `GET /dataset/analytics`")

    top_prods = analytics_data.get("top_products", [])
    cat_breakdown = analytics_data.get("category_breakdown", [])
    declining_prods = analytics_data.get("declining_products", [])

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.write("#### Top Products by Revenue")
        if top_prods:
            top_p_df = pd.DataFrame(top_prods)
            st.dataframe(top_p_df[["product_name", "category", "sales", "units", "profit"]], use_container_width=True)

    with p_col2:
        st.write("#### Revenue Share by Category")
        if cat_breakdown:
            cat_df = pd.DataFrame(cat_breakdown)
            fig_cat = px.pie(cat_df, names="category", values="sales", hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)

    st.write("#### Products with Largest Absolute Revenue Decline")
    if declining_prods:
        dec_df = pd.DataFrame(declining_prods)
        st.dataframe(
            dec_df[
                [
                    "product_name",
                    "category",
                    "prior_sales",
                    "current_sales",
                    "absolute_sales_change",
                    "percentage_sales_change",
                    "contribution_to_total_decline_pct",
                ]
            ],
            use_container_width=True,
        )
    else:
        st.info("No declining products observed in this comparison window.")


with tab_regions:
    st.subheader("Geographic & Territorial Breakdown")
    st.caption("Data source: `GET /dataset/analytics`")

    reg_list = analytics_data.get("regional_breakdown", [])
    if reg_list:
        reg_df = pd.DataFrame(reg_list)
        r1, r2 = st.columns(2)
        with r1:
            fig_r = px.bar(
                reg_df,
                x="region",
                y="sales",
                color="profit_margin_pct",
                labels={"sales": "Revenue ($)", "region": "Region", "profit_margin_pct": "Margin (%)"},
                title="Revenue by Territory",
                color_continuous_scale="Teal",
            )
            st.plotly_chart(fig_r, use_container_width=True)
        with r2:
            st.write("#### Territorial Statistics")
            st.dataframe(
                reg_df[
                    [
                        "region",
                        "sales",
                        "sales_share_pct",
                        "orders",
                        "units",
                        "profit",
                        "profit_margin_pct",
                    ]
                ],
                use_container_width=True,
            )


with tab_ai:
    st.subheader("🤖 Multi-Agent Business Intelligence Studio")
    st.caption("Workflow orchestrated via: `POST /analysis/run` and `GET /analysis/{id}`")
    st.markdown(
        "Ask a strategic business question to deploy the 5 specialized agents: "
        "**Data Agent**, **Analyst Agent**, **Strategy Agent**, **Verifier Agent**, and **Report Agent**."
    )

    preset_questions = [
        "Why did sales revenue change between recent quarters, and which products or regions experienced the largest declines?",
        "What are our top underperforming product lines and what pricing guardrails should we introduce?",
        "Which sales regions are contributing most to profitability and where are deep discounts destroying margin?",
    ]
    selected_preset = st.selectbox("Choose an Example Question or Write Your Own:", preset_questions)

    user_question = st.text_area("Your Business Question:", value=selected_preset, height=80)

    ai_col1, ai_col2 = st.columns([1, 3])
    with ai_col1:
        comp_mode = st.selectbox(
            "Comparison Mode",
            [
                "latest_vs_previous_quarter",
                "latest_vs_previous_month",
                "all_time_overview",
            ],
            index=0,
        )
    with ai_col2:
        max_recs = st.slider("Max Recommendations", min_value=1, max_value=8, value=4)

    if st.button("🚀 Run Multi-Agent Analysis via API", type="primary", use_container_width=True):
        with st.spinner("Dispatching HTTP POST request to `/analysis/run`..."):
            req_payload = {
                "business_question": user_question,
                "settings": {
                    "comparison_mode": comp_mode,
                    "max_recommendations": max_recs,
                },
            }


            summary_resp = call_api("POST", "/analysis/run", json_data=req_payload)

            if summary_resp:
                aid = summary_resp.get("analysis_id")

                full_state = call_api("GET", f"/analysis/{aid}")
                if full_state:
                    st.session_state["latest_analysis"] = full_state
                    st.success(f"Analysis completed successfully (Analysis ID: `{aid[:8]}`).")


    if "latest_analysis" in st.session_state:
        state = st.session_state["latest_analysis"]
        st.markdown("---")
        aid = state.get("analysis_id", "")
        st.write(f"### Analysis Results: `{aid[:8]}`")

        verifier_out = state.get("verifier_output", {})
        v_status = verifier_out.get("status", "unknown")

        if v_status == "verified":
            st.markdown('<span class="badge-verified">✓ MATHEMATICALLY VERIFIED</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="badge-warning">⚠️ STATUS: {v_status.upper()}</span>', unsafe_allow_html=True)

        trace = state.get("trace", {})
        st.write(f"**Execution Latency:** {trace.get('total_duration_seconds', 0.0):.2f}s")


        with st.expander("🔍 Multi-Agent Execution Trace & Step Latencies", expanded=True):
            trace_steps = trace.get("steps", [])
            for s in trace_steps:
                st.markdown(
                    f"**Step [{s.get('step_id')}] - {s.get('agent_name')}** (`{s.get('duration_seconds', 0.0):.2f}s` | "
                    f"Input: `{s.get('input_tokens', 0):,}` toks, Output: `{s.get('output_tokens', 0):,}` toks): "
                    f"*{s.get('output_summary')}*"
                )


        st.subheader("🪙 Per-Agent Token Usage (Gemini Inbuilt Tokenizer)")
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
            st.metric("Total Input Tokens", f"{trace.get('total_input_tokens', 0):,}")
        with t_col2:
            st.metric("Total Output Tokens", f"{trace.get('total_output_tokens', 0):,}")
        with t_col3:
            st.metric("Total Pipeline Tokens", f"{trace.get('total_tokens', 0):,}")

        token_by_agent = trace.get("token_usage_by_agent", {})
        if token_by_agent:
            token_rows = [
                {
                    "Agent Name": agent_name,
                    "Input Tokens": metrics.get("input_tokens", 0),
                    "Output Tokens": metrics.get("output_tokens", 0),
                    "Total Tokens": metrics.get("total_tokens", 0),
                }
                for agent_name, metrics in token_by_agent.items()
            ]
            st.dataframe(pd.DataFrame(token_rows), use_container_width=True)


        rep_out = state.get("report_output", {})
        if rep_out.get("executive_summary"):
            st.info(f"**Executive Summary:**\n\n{rep_out['executive_summary']}")


        analyst_out = state.get("analyst_output", {})
        findings = analyst_out.get("findings", [])
        if findings:
            st.subheader("Audited Empirical Findings")
            for f in findings:
                st.markdown(
                    f"- **[{f.get('id')}] {f.get('title')}:** Computed `{f.get('metric_name')}` = "
                    f"**${f.get('computed_value', 0.0):,.2f}** ({f.get('notes', '')})"
                )


        strat_out = state.get("strategy_output", {})
        recommendations = strat_out.get("recommendations", [])
        if recommendations:
            st.subheader("Prioritized Strategic Recommendations")
            for r in recommendations:
                with st.expander(f"📌 {r.get('id')}: {r.get('title')} [Impact: {r.get('potential_impact', '').upper()}]"):
                    st.write(f"**Action:** {r.get('action')}")
                    st.write(f"**Rationale:** {r.get('rationale')}")
                    st.write(f"**Linked Findings:** `{', '.join(r.get('supporting_finding_ids', []))}`")
                    if r.get("assumptions"):
                        st.write(f"**Assumptions:** {'; '.join(r['assumptions'])}")
                    if r.get("suggested_follow_up"):
                        st.write(f"**Suggested Validation:** {'; '.join(r['suggested_follow_up'])}")


with tab_reports:
    st.subheader("Executive Markdown Report & Data Exports")
    st.caption("Data source: `GET /analysis/{id}/report/raw`")

    if "latest_analysis" in st.session_state:
        state = st.session_state["latest_analysis"]
        aid = state.get("analysis_id", "")
        rep_out = state.get("report_output", {})
        md_report = rep_out.get("markdown_report", "")

        if md_report:
            st.download_button(
                label="📥 Download Executive Report (.md)",
                data=md_report,
                file_name=f"business_intelligence_report_{aid[:8]}.md",
                mime="text/markdown",
            )
            st.markdown(md_report)
        else:
            st.info("No report generated yet.")
    else:
        st.info("Run an analysis in the **AI Multi-Agent Studio** tab to view and download full executive reports.")
