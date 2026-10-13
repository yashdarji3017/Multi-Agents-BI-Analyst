"""Deterministic trend analysis across monthly and quarterly intervals."""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from pydantic import BaseModel

from businessinsight.analytics.metrics import safe_percentage_change


class TrendDataPoint(BaseModel):
    """Single period observation within a time series."""

    period: str
    sales: float
    orders: int
    units: int
    aov: float
    profit: float = 0.0
    profit_margin_pct: float = 0.0
    prior_period_sales: float = 0.0
    absolute_sales_change: float = 0.0
    percentage_sales_change: float | None = None
    is_complete_period: bool = True


class TrendAnalysisResult(BaseModel):
    """Collection of trend data points and summary statistics."""

    interval: str
    data_points: List[TrendDataPoint]
    highest_period: Dict[str, Any]
    lowest_period: Dict[str, Any]
    latest_complete_period: str
    previous_complete_period: str
    period_over_period_growth_pct: float | None = None


def analyze_monthly_trend(df: pd.DataFrame) -> TrendAnalysisResult:
    """Computes monthly aggregated sales, orders, AOV, and MoM trends."""
    if df.empty:
        return TrendAnalysisResult(
            interval="monthly",
            data_points=[],
            highest_period={},
            lowest_period={},
            latest_complete_period="",
            previous_complete_period="",
        )


    grouped = (
        df.groupby("year_month")
        .agg(
            sales=("sales", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
            profit=("profit", "sum") if "profit" in df.columns else ("sales", lambda x: 0.0),
        )
        .reset_index()
        .sort_values("year_month")
    )

    points: List[TrendDataPoint] = []
    prior_sales = 0.0

    for idx, row in grouped.iterrows():
        p_sales = float(np.round(row["sales"], 2))
        p_orders = int(row["orders"])
        p_units = int(row["units"])
        p_profit = float(np.round(row["profit"], 2))
        p_aov = float(np.round(p_sales / p_orders, 2)) if p_orders > 0 else 0.0
        p_margin = float(np.round((p_profit / p_sales) * 100, 2)) if p_sales > 0 else 0.0

        if idx == 0:
            abs_change = 0.0
            pct_change = None
        else:
            abs_change = float(np.round(p_sales - prior_sales, 2))
            pct_change = safe_percentage_change(p_sales, prior_sales)

        points.append(
            TrendDataPoint(
                period=str(row["year_month"]),
                sales=p_sales,
                orders=p_orders,
                units=p_units,
                aov=p_aov,
                profit=p_profit,
                profit_margin_pct=p_margin,
                prior_period_sales=prior_sales if idx > 0 else 0.0,
                absolute_sales_change=abs_change,
                percentage_sales_change=pct_change,
                is_complete_period=True,
            )
        )
        prior_sales = p_sales

    highest = max(points, key=lambda x: x.sales).model_dump() if points else {}
    lowest = min(points, key=lambda x: x.sales).model_dump() if points else {}

    latest = points[-1].period if points else ""
    prev = points[-2].period if len(points) > 1 else ""
    pop_growth = points[-1].percentage_sales_change if points else None

    return TrendAnalysisResult(
        interval="monthly",
        data_points=points,
        highest_period=highest,
        lowest_period=lowest,
        latest_complete_period=latest,
        previous_complete_period=prev,
        period_over_period_growth_pct=pop_growth,
    )


def analyze_quarterly_trend(df: pd.DataFrame) -> TrendAnalysisResult:
    """Computes quarterly aggregated sales, orders, AOV, and QoQ trends."""
    if df.empty:
        return TrendAnalysisResult(
            interval="quarterly",
            data_points=[],
            highest_period={},
            lowest_period={},
            latest_complete_period="",
            previous_complete_period="",
        )

    grouped = (
        df.groupby("quarter")
        .agg(
            sales=("sales", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
            profit=("profit", "sum") if "profit" in df.columns else ("sales", lambda x: 0.0),
        )
        .reset_index()
        .sort_values("quarter")
    )

    points: List[TrendDataPoint] = []
    prior_sales = 0.0

    for idx, row in grouped.iterrows():
        p_sales = float(np.round(row["sales"], 2))
        p_orders = int(row["orders"])
        p_units = int(row["units"])
        p_profit = float(np.round(row["profit"], 2))
        p_aov = float(np.round(p_sales / p_orders, 2)) if p_orders > 0 else 0.0
        p_margin = float(np.round((p_profit / p_sales) * 100, 2)) if p_sales > 0 else 0.0

        if idx == 0:
            abs_change = 0.0
            pct_change = None
        else:
            abs_change = float(np.round(p_sales - prior_sales, 2))
            pct_change = safe_percentage_change(p_sales, prior_sales)

        points.append(
            TrendDataPoint(
                period=str(row["quarter"]),
                sales=p_sales,
                orders=p_orders,
                units=p_units,
                aov=p_aov,
                profit=p_profit,
                profit_margin_pct=p_margin,
                prior_period_sales=prior_sales if idx > 0 else 0.0,
                absolute_sales_change=abs_change,
                percentage_sales_change=pct_change,
                is_complete_period=True,
            )
        )
        prior_sales = p_sales

    highest = max(points, key=lambda x: x.sales).model_dump() if points else {}
    lowest = min(points, key=lambda x: x.sales).model_dump() if points else {}

    latest = points[-1].period if points else ""
    prev = points[-2].period if len(points) > 1 else ""
    pop_growth = points[-1].percentage_sales_change if points else None

    return TrendAnalysisResult(
        interval="quarterly",
        data_points=points,
        highest_period=highest,
        lowest_period=lowest,
        latest_complete_period=latest,
        previous_complete_period=prev,
        period_over_period_growth_pct=pop_growth,
    )
