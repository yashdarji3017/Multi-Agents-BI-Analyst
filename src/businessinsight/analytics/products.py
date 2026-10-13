"""Deterministic product and category performance analytics."""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel

from businessinsight.analytics.metrics import calculate_revenue_contribution, safe_percentage_change


class ProductMetric(BaseModel):
    """Metrics for an individual product."""

    product_name: str
    category: str
    sub_category: Optional[str] = None
    sales: float
    units: int
    orders: int
    profit: float = 0.0
    profit_margin_pct: float = 0.0


class ProductDeclineItem(BaseModel):
    """Detailed record for a product experiencing revenue decline between periods."""

    product_name: str
    category: str
    prior_sales: float
    current_sales: float
    absolute_sales_change: float
    percentage_sales_change: Optional[float]
    prior_units: int
    current_units: int
    prior_profit: float = 0.0
    current_profit: float = 0.0
    contribution_to_total_decline_pct: Optional[float] = None


class CategoryPerformance(BaseModel):
    """Aggregated performance for a product category."""

    category: str
    sales: float
    sales_share_pct: float
    orders: int
    units: int
    profit: float = 0.0
    profit_margin_pct: float = 0.0


class ProductAnalysisResult(BaseModel):
    """Comprehensive product performance analysis."""

    top_products_by_sales: List[ProductMetric]
    declining_products: List[ProductDeclineItem]
    category_breakdown: List[CategoryPerformance]
    total_products_count: int
    declining_products_count: int
    overall_sales_change: float = 0.0


def analyze_product_performance(
    df_current: pd.DataFrame,
    df_prior: Optional[pd.DataFrame] = None,
    top_n: int = 10,
) -> ProductAnalysisResult:
    """Analyzes product sales, identifies top performers, and pinpoints largest absolute declines."""
    if df_current.empty:
        return ProductAnalysisResult(
            top_products_by_sales=[],
            declining_products=[],
            category_breakdown=[],
            total_products_count=0,
            declining_products_count=0,
        )


    current_agg = (
        df_current.groupby(["product_name", "category"])
        .agg(
            sales=("sales", "sum"),
            units=("quantity", "sum") if "quantity" in df_current.columns else ("sales", "count"),
            orders=("order_id", "nunique"),
            profit=("profit", "sum") if "profit" in df_current.columns else ("sales", lambda x: 0.0),
        )
        .reset_index()
    )

    total_current_sales = current_agg["sales"].sum()


    top_curr = current_agg.sort_values("sales", ascending=False).head(top_n)
    top_products = [
        ProductMetric(
            product_name=str(row["product_name"]),
            category=str(row["category"]),
            sales=float(np.round(row["sales"], 2)),
            units=int(row["units"]),
            orders=int(row["orders"]),
            profit=float(np.round(row["profit"], 2)),
            profit_margin_pct=float(np.round((row["profit"] / row["sales"]) * 100, 2))
            if row["sales"] > 0
            else 0.0,
        )
        for _, row in top_curr.iterrows()
    ]


    cat_agg = (
        df_current.groupby("category")
        .agg(
            sales=("sales", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum") if "quantity" in df_current.columns else ("sales", "count"),
            profit=("profit", "sum") if "profit" in df_current.columns else ("sales", lambda x: 0.0),
        )
        .reset_index()
        .sort_values("sales", ascending=False)
    )

    categories = [
        CategoryPerformance(
            category=str(row["category"]),
            sales=float(np.round(row["sales"], 2)),
            sales_share_pct=float(np.round((row["sales"] / total_current_sales) * 100, 2))
            if total_current_sales > 0
            else 0.0,
            orders=int(row["orders"]),
            units=int(row["units"]),
            profit=float(np.round(row["profit"], 2)),
            profit_margin_pct=float(np.round((row["profit"] / row["sales"]) * 100, 2))
            if row["sales"] > 0
            else 0.0,
        )
        for _, row in cat_agg.iterrows()
    ]


    declining_items: List[ProductDeclineItem] = []
    total_decline_pool = 0.0
    overall_change = 0.0

    if df_prior is not None and not df_prior.empty:
        prior_agg = (
            df_prior.groupby(["product_name", "category"])
            .agg(
                sales=("sales", "sum"),
                units=("quantity", "sum") if "quantity" in df_prior.columns else ("sales", "count"),
                profit=("profit", "sum") if "profit" in df_prior.columns else ("sales", lambda x: 0.0),
            )
            .reset_index()
        )

        merged = pd.merge(
            prior_agg,
            current_agg,
            on=["product_name", "category"],
            how="outer",
            suffixes=("_prior", "_curr"),
        ).fillna(0.0)

        merged["abs_change"] = merged["sales_curr"] - merged["sales_prior"]
        total_prior_sales = prior_agg["sales"].sum()
        overall_change = float(np.round(total_current_sales - total_prior_sales, 2))


        declining_df = merged[merged["abs_change"] < 0].sort_values("abs_change", ascending=True)


        total_decline_pool = abs(float(declining_df["abs_change"].sum()))

        for _, row in declining_df.head(top_n).iterrows():
            abs_chg = float(np.round(row["abs_change"], 2))
            prior_s = float(np.round(row["sales_prior"], 2))
            curr_s = float(np.round(row["sales_curr"], 2))
            pct_chg = safe_percentage_change(curr_s, prior_s)

            contrib_pct = (
                float(np.round((abs(abs_chg) / total_decline_pool) * 100, 2))
                if total_decline_pool > 0
                else None
            )

            declining_items.append(
                ProductDeclineItem(
                    product_name=str(row["product_name"]),
                    category=str(row["category"]),
                    prior_sales=prior_s,
                    current_sales=curr_s,
                    absolute_sales_change=abs_chg,
                    percentage_sales_change=pct_chg,
                    prior_units=int(row["units_prior"]),
                    current_units=int(row["units_curr"]),
                    prior_profit=float(np.round(row["profit_prior"], 2)),
                    current_profit=float(np.round(row["profit_curr"], 2)),
                    contribution_to_total_decline_pct=contrib_pct,
                )
            )

    return ProductAnalysisResult(
        top_products_by_sales=top_products,
        declining_products=declining_items,
        category_breakdown=categories,
        total_products_count=len(current_agg),
        declining_products_count=len(declining_items),
        overall_sales_change=overall_change,
    )
