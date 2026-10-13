"""Interactive Plotly charts and export utilities for business intelligence."""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from businessinsight.config import settings
from businessinsight.workflow.schemas import AnalystAgentOutput

logger = logging.getLogger(__name__)


def create_sales_trend_chart(analyst_output: AnalystAgentOutput) -> go.Figure:
    """Builds interactive sales trend chart over time with period markers."""
    trend = analyst_output.trend_analysis
    if not trend or not trend.data_points:
        fig = go.Figure()
        fig.add_annotation(text="No trend data available", showarrow=False)
        return fig

    df_plot = pd.DataFrame([dp.model_dump() for dp in trend.data_points])

    fig = go.Figure()


    fig.add_trace(
        go.Bar(
            x=df_plot["period"],
            y=df_plot["sales"],
            name="Revenue ($)",
            marker_color="#2563EB",
            opacity=0.85,
        )
    )


    fig.add_trace(
        go.Scatter(
            x=df_plot["period"],
            y=df_plot["aov"],
            name="AOV ($)",
            yaxis="y2",
            line=dict(color="#10B981", width=3),
            mode="lines+markers",
        )
    )

    fig.update_layout(
        title=f"Sales Revenue & Average Order Value Trend ({trend.interval.capitalize()})",
        xaxis=dict(title="Period", tickangle=-45),
        yaxis=dict(title="Revenue ($)", showgrid=True),
        yaxis2=dict(
            title="AOV ($)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return fig


def create_regional_sales_chart(analyst_output: AnalystAgentOutput) -> go.Figure:
    """Builds regional sales comparison chart."""
    regions = analyst_output.regional_breakdown
    if not regions:
        fig = go.Figure()
        fig.add_annotation(text="No regional data available", showarrow=False)
        return fig

    df_reg = pd.DataFrame([r.model_dump() for r in regions])

    fig = px.bar(
        df_reg,
        x="region",
        y="sales",
        color="profit_margin_pct",
        color_continuous_scale="Viridis",
        labels={"sales": "Revenue ($)", "region": "Region", "profit_margin_pct": "Margin (%)"},
        title="Revenue by Geographic Region with Profit Margin Indicator",
    )
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=60, b=40))
    return fig


def create_category_pie_chart(analyst_output: AnalystAgentOutput) -> go.Figure:
    """Builds product category market share donut chart."""
    cats = analyst_output.category_breakdown
    if not cats:
        fig = go.Figure()
        fig.add_annotation(text="No category data available", showarrow=False)
        return fig

    df_cat = pd.DataFrame([c.model_dump() for c in cats])

    fig = px.pie(
        df_cat,
        names="category",
        values="sales",
        hole=0.45,
        title="Revenue Share by Product Category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(template="plotly_white", margin=dict(l=30, r=30, t=50, b=30))
    return fig


def create_declining_products_chart(analyst_output: AnalystAgentOutput) -> go.Figure:
    """Builds horizontal bar chart of top declining products."""
    decliners = analyst_output.declining_products
    if not decliners:
        fig = go.Figure()
        fig.add_annotation(text="No declining products recorded", showarrow=False)
        return fig

    df_dec = pd.DataFrame([d.model_dump() for d in decliners[:10]])
    df_dec["short_name"] = df_dec["product_name"].apply(lambda x: x[:30] + "..." if len(x) > 30 else x)
    df_dec["abs_decline"] = df_dec["absolute_sales_change"].abs()

    fig = px.bar(
        df_dec.sort_values("abs_decline", ascending=True),
        x="abs_decline",
        y="short_name",
        orientation="h",
        color="category",
        title="Top Products with Largest Absolute Revenue Decline ($)",
        labels={"abs_decline": "Absolute Decline ($)", "short_name": "Product Name"},
    )
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=50, b=40))
    return fig


def export_charts_for_analysis(
    analyst_output: AnalystAgentOutput,
    analysis_id: str,
    output_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """Generates and writes interactive HTML chart artifacts to local disk.

    Returns mapping of chart_key -> local_file_path.
    """
    target_dir = output_dir or settings.charts_output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    charts = {
        "sales_trend": create_sales_trend_chart(analyst_output),
        "regional_sales": create_regional_sales_chart(analyst_output),
        "category_share": create_category_pie_chart(analyst_output),
        "product_declines": create_declining_products_chart(analyst_output),
    }

    saved_paths: Dict[str, str] = {}
    for name, fig in charts.items():
        file_path = target_dir / f"{analysis_id[:8]}_{name}.html"
        try:
            fig.write_html(str(file_path), include_plotlyjs="cdn")
            saved_paths[name] = str(file_path)
        except Exception as e:
            logger.warning(f"Could not write chart {name} to file: {e}")

    return saved_paths
