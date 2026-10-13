"""Deterministic financial and sales metrics calculations."""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel


class PeriodComparison(BaseModel):
    """Encapsulates period-over-period financial comparison."""

    prior_period_label: str
    current_period_label: str
    prior_sales: float
    current_sales: float
    absolute_sales_change: float
    percentage_sales_change: Optional[float]
    prior_orders: int
    current_orders: int
    absolute_order_change: int
    percentage_order_change: Optional[float]
    prior_aov: float
    current_aov: float
    absolute_aov_change: float
    percentage_aov_change: Optional[float]
    prior_profit: Optional[float] = None
    current_profit: Optional[float] = None
    absolute_profit_change: Optional[float] = None
    prior_profit_margin_pct: Optional[float] = None
    current_profit_margin_pct: Optional[float] = None


class SummaryKPIs(BaseModel):
    """High-level Key Performance Indicators for an analyzed dataset or slice."""

    total_sales: float
    distinct_orders: int
    total_units_sold: int
    average_order_value: float
    total_profit: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    average_discount_pct: Optional[float] = None
    date_start: str
    date_end: str
    total_records: int


def calculate_revenue(df: pd.DataFrame) -> float:
    """Calculates total sales revenue deterministically."""
    if df.empty or "sales" not in df.columns:
        return 0.0
    return float(np.round(df["sales"].sum(), 2))


def analyze_order_volume(df: pd.DataFrame) -> int:
    """Calculates distinct order count without double-counting line items."""
    if df.empty or "order_id" not in df.columns:
        return 0
    return int(df["order_id"].nunique())


def analyze_average_order_value(df: pd.DataFrame) -> float:
    """Calculates Average Order Value (AOV = Total Sales / Distinct Orders)."""
    if df.empty:
        return 0.0
    total_sales = calculate_revenue(df)
    orders = analyze_order_volume(df)
    if orders <= 0:
        return 0.0
    return float(np.round(total_sales / orders, 2))


def calculate_kpis(df: pd.DataFrame) -> SummaryKPIs:
    """Computes comprehensive KPIs for the given DataFrame slice."""
    if df.empty:
        return SummaryKPIs(
            total_sales=0.0,
            distinct_orders=0,
            total_units_sold=0,
            average_order_value=0.0,
            date_start="N/A",
            date_end="N/A",
            total_records=0,
        )

    total_sales = calculate_revenue(df)
    orders = analyze_order_volume(df)
    aov = analyze_average_order_value(df)

    units_sold = int(df["quantity"].sum()) if "quantity" in df.columns else len(df)

    profit = None
    margin = None
    if "profit" in df.columns:
        profit = float(np.round(df["profit"].sum(), 2))
        if total_sales > 0:
            margin = float(np.round((profit / total_sales) * 100, 2))

    avg_discount = None
    if "discount" in df.columns:
        avg_discount = float(np.round(df["discount"].mean() * 100, 2))

    date_start = df["order_date"].min().strftime("%Y-%m-%d") if "order_date" in df.columns else "N/A"
    date_end = df["order_date"].max().strftime("%Y-%m-%d") if "order_date" in df.columns else "N/A"

    return SummaryKPIs(
        total_sales=total_sales,
        distinct_orders=orders,
        total_units_sold=units_sold,
        average_order_value=aov,
        total_profit=profit,
        profit_margin_pct=margin,
        average_discount_pct=avg_discount,
        date_start=date_start,
        date_end=date_end,
        total_records=len(df),
    )


def safe_percentage_change(current: float, prior: float) -> Optional[float]:
    """Computes percentage change safely without dividing by zero.

    Returns ((current - prior) / prior) * 100 or None if prior is 0.
    """
    if prior == 0:
        return None
    return float(np.round(((current - prior) / abs(prior)) * 100, 2))


def compare_periods(
    df_prior: pd.DataFrame,
    df_current: pd.DataFrame,
    prior_label: str = "Prior Period",
    current_label: str = "Current Period",
) -> PeriodComparison:
    """Compares two period DataFrames deterministically."""
    prior_sales = calculate_revenue(df_prior)
    current_sales = calculate_revenue(df_current)
    abs_sales_change = float(np.round(current_sales - prior_sales, 2))
    pct_sales_change = safe_percentage_change(current_sales, prior_sales)

    prior_orders = analyze_order_volume(df_prior)
    current_orders = analyze_order_volume(df_current)
    abs_order_change = current_orders - prior_orders
    pct_order_change = safe_percentage_change(float(current_orders), float(prior_orders))

    prior_aov = analyze_average_order_value(df_prior)
    current_aov = analyze_average_order_value(df_current)
    abs_aov_change = float(np.round(current_aov - prior_aov, 2))
    pct_aov_change = safe_percentage_change(current_aov, prior_aov)


    prior_profit = None
    current_profit = None
    abs_profit_change = None
    prior_margin = None
    current_margin = None

    if "profit" in df_prior.columns and "profit" in df_current.columns:
        prior_profit = float(np.round(df_prior["profit"].sum(), 2)) if not df_prior.empty else 0.0
        current_profit = float(np.round(df_current["profit"].sum(), 2)) if not df_current.empty else 0.0
        abs_profit_change = float(np.round(current_profit - prior_profit, 2))
        if prior_sales > 0:
            prior_margin = float(np.round((prior_profit / prior_sales) * 100, 2))
        if current_sales > 0:
            current_margin = float(np.round((current_profit / current_sales) * 100, 2))

    return PeriodComparison(
        prior_period_label=prior_label,
        current_period_label=current_label,
        prior_sales=prior_sales,
        current_sales=current_sales,
        absolute_sales_change=abs_sales_change,
        percentage_sales_change=pct_sales_change,
        prior_orders=prior_orders,
        current_orders=current_orders,
        absolute_order_change=abs_order_change,
        percentage_order_change=pct_order_change,
        prior_aov=prior_aov,
        current_aov=current_aov,
        absolute_aov_change=abs_aov_change,
        percentage_aov_change=pct_aov_change,
        prior_profit=prior_profit,
        current_profit=current_profit,
        absolute_profit_change=abs_profit_change,
        prior_profit_margin_pct=prior_margin,
        current_profit_margin_pct=current_margin,
    )


def calculate_revenue_contribution(
    segment_sales_change: float,
    total_sales_change: float,
) -> Dict[str, Any]:
    """Calculates both absolute change and percentage contribution to overall revenue change.

    Handles edge cases where total_sales_change is zero or where gains and losses offset.
    """
    if total_sales_change == 0:
        pct_contrib = 0.0
    else:
        pct_contrib = float(np.round((segment_sales_change / total_sales_change) * 100, 2))

    return {
        "absolute_change": float(np.round(segment_sales_change, 2)),
        "percentage_contribution": pct_contrib,
        "is_offsetting": (segment_sales_change > 0 > total_sales_change)
        or (segment_sales_change < 0 < total_sales_change),
    }
