"""Deterministic regional sales performance analytics."""

from typing import List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel

from businessinsight.analytics.metrics import calculate_revenue_contribution, safe_percentage_change


class RegionMetric(BaseModel):
    """Performance metrics for an individual geographic region."""

    region: str
    sales: float
    sales_share_pct: float
    orders: int
    units: int
    aov: float
    profit: float = 0.0
    profit_margin_pct: float = 0.0
    prior_sales: Optional[float] = None
    absolute_sales_change: Optional[float] = None
    percentage_sales_change: Optional[float] = None
    contribution_to_total_change_pct: Optional[float] = None


class RegionalAnalysisResult(BaseModel):
    """Comprehensive regional performance analysis."""

    regions: List[RegionMetric]
    top_region_by_sales: str
    top_declining_region: Optional[str] = None
    overall_sales_change: float = 0.0


def analyze_regional_performance(
    df_current: pd.DataFrame,
    df_prior: Optional[pd.DataFrame] = None,
) -> RegionalAnalysisResult:
    """Analyzes sales across geographic territories and measures regional shifts."""
    if df_current.empty or "region" not in df_current.columns:
        return RegionalAnalysisResult(regions=[], top_region_by_sales="", overall_sales_change=0.0)

    curr_agg = (
        df_current.groupby("region")
        .agg(
            sales=("sales", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum") if "quantity" in df_current.columns else ("sales", "count"),
            profit=("profit", "sum") if "profit" in df_current.columns else ("sales", lambda x: 0.0),
        )
        .reset_index()
    )

    total_curr_sales = curr_agg["sales"].sum()

    prior_agg = None
    total_prior_sales = 0.0
    if df_prior is not None and not df_prior.empty and "region" in df_prior.columns:
        prior_agg = (
            df_prior.groupby("region")
            .agg(
                sales=("sales", "sum"),
                orders=("order_id", "nunique"),
                units=("quantity", "sum") if "quantity" in df_prior.columns else ("sales", "count"),
                profit=("profit", "sum") if "profit" in df_prior.columns else ("sales", lambda x: 0.0),
            )
            .reset_index()
        )
        total_prior_sales = prior_agg["sales"].sum()

    overall_change = float(np.round(total_curr_sales - total_prior_sales, 2)) if prior_agg is not None else 0.0

    regions_list: List[RegionMetric] = []
    top_declining_reg = None
    largest_decline_amount = 0.0

    for _, row in curr_agg.iterrows():
        reg = str(row["region"])
        s_curr = float(np.round(row["sales"], 2))
        o_curr = int(row["orders"])
        u_curr = int(row["units"])
        p_curr = float(np.round(row["profit"], 2))
        aov_curr = float(np.round(s_curr / o_curr, 2)) if o_curr > 0 else 0.0
        margin_curr = float(np.round((p_curr / s_curr) * 100, 2)) if s_curr > 0 else 0.0

        share_pct = float(np.round((s_curr / total_curr_sales) * 100, 2)) if total_curr_sales > 0 else 0.0

        s_prior = None
        abs_chg = None
        pct_chg = None
        contrib_pct = None

        if prior_agg is not None:
            prior_match = prior_agg[prior_agg["region"] == reg]
            if not prior_match.empty:
                s_prior = float(np.round(prior_match["sales"].iloc[0], 2))
            else:
                s_prior = 0.0

            abs_chg = float(np.round(s_curr - s_prior, 2))
            pct_chg = safe_percentage_change(s_curr, s_prior)

            if overall_change != 0.0:
                contrib = calculate_revenue_contribution(abs_chg, overall_change)
                contrib_pct = contrib["percentage_contribution"]

            if abs_chg < largest_decline_amount:
                largest_decline_amount = abs_chg
                top_declining_reg = reg

        regions_list.append(
            RegionMetric(
                region=reg,
                sales=s_curr,
                sales_share_pct=share_pct,
                orders=o_curr,
                units=u_curr,
                aov=aov_curr,
                profit=p_curr,
                profit_margin_pct=margin_curr,
                prior_sales=s_prior,
                absolute_sales_change=abs_chg,
                percentage_sales_change=pct_chg,
                contribution_to_total_change_pct=contrib_pct,
            )
        )


    regions_list.sort(key=lambda r: r.sales, reverse=True)
    top_reg = regions_list[0].region if regions_list else ""

    return RegionalAnalysisResult(
        regions=regions_list,
        top_region_by_sales=top_reg,
        top_declining_region=top_declining_reg,
        overall_sales_change=overall_change,
    )
