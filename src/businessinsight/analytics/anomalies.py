"""Deterministic anomaly detection in transactions, daily revenue, and margins."""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from pydantic import BaseModel


class AnomalyItem(BaseModel):
    """Encapsulates an identified analytical anomaly."""

    anomaly_type: str
    description: str
    metric_value: float
    expected_range: str
    severity: str
    details: Dict[str, Any] = {}


def detect_anomalies(df: pd.DataFrame) -> List[AnomalyItem]:
    """Detects statistical revenue spikes, margin irregularities, and volume anomalies deterministically."""
    if df.empty or "sales" not in df.columns:
        return []

    anomalies: List[AnomalyItem] = []


    if "order_date" in df.columns:
        daily_sales = df.groupby(df["order_date"].dt.date)["sales"].sum()
        if len(daily_sales) >= 10:
            q25 = daily_sales.quantile(0.25)
            q75 = daily_sales.quantile(0.75)
            iqr = q75 - q25
            upper_bound = q75 + (1.5 * iqr)

            spikes = daily_sales[daily_sales > upper_bound]
            for date_val, val in spikes.items():
                anomalies.append(
                    AnomalyItem(
                        anomaly_type="daily_sales_spike",
                        description=f"Unusually high sales on {date_val}: ${val:,.2f}",
                        metric_value=float(np.round(val, 2)),
                        expected_range=f"IQR Upper Threshold: ${upper_bound:,.2f}",
                        severity="medium",
                        details={"date": str(date_val), "sales": float(val)},
                    )
                )


    sales_mean = df["sales"].mean()
    sales_std = df["sales"].std()
    if pd.notna(sales_std) and sales_std > 0:
        high_sales_threshold = sales_mean + (3 * sales_std)
        large_transactions = df[df["sales"] > high_sales_threshold]
        for _, row in large_transactions.head(5).iterrows():
            anomalies.append(
                AnomalyItem(
                    anomaly_type="outlier_transaction",
                    description=(
                        f"Outlier order line item for '{row.get('product_name', 'Unknown')[:35]}...' "
                        f"with ${row['sales']:,.2f} in sales."
                    ),
                    metric_value=float(np.round(row["sales"], 2)),
                    expected_range=f"3-Sigma Threshold: ${high_sales_threshold:,.2f}",
                    severity="info",
                    details={
                        "order_id": str(row.get("order_id", "")),
                        "product_name": str(row.get("product_name", "")),
                    },
                )
            )


    if "profit" in df.columns:
        severe_losses = df[df["profit"] < -500.0].sort_values("profit", ascending=True)
        for _, row in severe_losses.head(5).iterrows():
            anomalies.append(
                AnomalyItem(
                    anomaly_type="severe_negative_profit",
                    description=(
                        f"Severe loss transaction on '{row.get('product_name', 'Unknown')[:35]}...': "
                        f"${row['profit']:,.2f} loss (Sales: ${row['sales']:,.2f}, Discount: {row.get('discount', 0)*100:.0f}%)."
                    ),
                    metric_value=float(np.round(row["profit"], 2)),
                    expected_range="Profit >= $0.00",
                    severity="high",
                    details={
                        "order_id": str(row.get("order_id", "")),
                        "discount": float(row.get("discount", 0.0)),
                    },
                )
            )


    if "discount" in df.columns:
        high_discounts = df[df["discount"] >= 0.6]
        if len(high_discounts) > 0:
            count = len(high_discounts)
            avg_loss = high_discounts["profit"].sum() if "profit" in high_discounts.columns else 0.0
            anomalies.append(
                AnomalyItem(
                    anomaly_type="extreme_discounting",
                    description=(
                        f"{count} transactions had deep discounts of 60% or higher, "
                        f"accumulating ${avg_loss:,.2f} in total profit impact."
                    ),
                    metric_value=float(count),
                    expected_range="Discounts < 60%",
                    severity="high" if avg_loss < 0 else "medium",
                    details={"count": count, "total_profit_impact": float(np.round(avg_loss, 2))},
                )
            )

    return anomalies
