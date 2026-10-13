"""Analytics package exposing deterministic calculations and verification tools."""

from .anomalies import AnomalyItem, detect_anomalies
from .metrics import (
    PeriodComparison,
    SummaryKPIs,
    analyze_average_order_value,
    analyze_order_volume,
    calculate_kpis,
    calculate_revenue,
    calculate_revenue_contribution,
    compare_periods,
    safe_percentage_change,
)
from .products import (
    CategoryPerformance,
    ProductAnalysisResult,
    ProductDeclineItem,
    ProductMetric,
    analyze_product_performance,
)
from .profiling import profile_dataset, validate_sales_schema
from .regions import (
    RegionalAnalysisResult,
    RegionMetric,
    analyze_regional_performance,
)
from .trends import (
    TrendAnalysisResult,
    TrendDataPoint,
    analyze_monthly_trend,
    analyze_quarterly_trend,
)
from .validation import (
    FindingVerificationResult,
    VerificationDiscrepancy,
    validate_finding,
    verify_period_percentage_change,
)

__all__ = [
    "profile_dataset",
    "validate_sales_schema",
    "calculate_revenue",
    "analyze_order_volume",
    "analyze_average_order_value",
    "calculate_kpis",
    "compare_periods",
    "calculate_revenue_contribution",
    "safe_percentage_change",
    "PeriodComparison",
    "SummaryKPIs",
    "analyze_monthly_trend",
    "analyze_quarterly_trend",
    "TrendDataPoint",
    "TrendAnalysisResult",
    "analyze_product_performance",
    "ProductMetric",
    "ProductDeclineItem",
    "CategoryPerformance",
    "ProductAnalysisResult",
    "analyze_regional_performance",
    "RegionMetric",
    "RegionalAnalysisResult",
    "detect_anomalies",
    "AnomalyItem",
    "validate_finding",
    "verify_period_percentage_change",
    "VerificationDiscrepancy",
    "FindingVerificationResult",
]
