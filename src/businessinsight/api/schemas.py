"""FastAPI request and response Pydantic schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from businessinsight.analytics import (
    AnomalyItem,
    CategoryPerformance,
    PeriodComparison,
    ProductDeclineItem,
    ProductMetric,
    RegionMetric,
    SummaryKPIs,
    TrendAnalysisResult,
)
from businessinsight.workflow.schemas import AnalysisSettings


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "healthy"
    service: str = "BusinessInsight AI"
    version: str = "0.1.0"
    database: str = "None (In-Memory Processing)"
    dataset_configured: bool
    dataset_exists: bool
    maf_gemini_ready: bool


class RunAnalysisRequest(BaseModel):
    """Request payload to initiate a multi-agent analysis."""

    business_question: str = Field(
        ...,
        description="The business inquiry or question to analyze",
        examples=["Why did revenue decline in the latest quarter and which regions were most affected?"],
    )
    settings: Optional[AnalysisSettings] = Field(
        default=None,
        description="Optional analysis configurations, date filters, or comparison modes",
    )


class AnalysisSummaryResponse(BaseModel):
    """Summary response returned immediately upon running analysis."""

    analysis_id: str
    business_question: str
    status: str
    duration_seconds: Optional[float] = None
    verification_status: Optional[str] = None
    executive_summary: Optional[str] = None
    total_sales: Optional[float] = None
    findings_count: int = 0
    recommendations_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    token_usage_by_agent: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class DatasetAnalyticsResponse(BaseModel):
    """Structured analytical response for interactive dashboard reporting."""

    kpis: SummaryKPIs
    monthly_trend: TrendAnalysisResult
    quarterly_trend: TrendAnalysisResult
    period_comparison: Optional[PeriodComparison] = None
    top_products: List[ProductMetric] = Field(default_factory=list)
    declining_products: List[ProductDeclineItem] = Field(default_factory=list)
    category_breakdown: List[CategoryPerformance] = Field(default_factory=list)
    regional_breakdown: List[RegionMetric] = Field(default_factory=list)
    anomalies: List[AnomalyItem] = Field(default_factory=list)
    available_categories: List[str] = Field(default_factory=list)
    available_regions: List[str] = Field(default_factory=list)
    min_date: Optional[str] = None
    max_date: Optional[str] = None
