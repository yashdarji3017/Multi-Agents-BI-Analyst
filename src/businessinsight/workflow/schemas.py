"""Pydantic v2 schemas for agent inputs, outputs, and workflow states."""

from enum import Enum
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
    VerificationDiscrepancy,
)
from businessinsight.data.validators import DatasetProfile


class ComparisonMode(str, Enum):
    """Supported temporal comparison intervals."""

    LATEST_VS_PREVIOUS_QUARTER = "latest_vs_previous_quarter"
    LATEST_VS_PREVIOUS_MONTH = "latest_vs_previous_month"
    YEAR_OVER_YEAR_LATEST_QUARTER = "year_over_year_latest_quarter"
    ALL_TIME_OVERVIEW = "all_time_overview"


class AnalysisSettings(BaseModel):
    """Configurable settings for an analysis execution run."""

    comparison_mode: ComparisonMode = ComparisonMode.LATEST_VS_PREVIOUS_QUARTER
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    product_category_filter: Optional[str] = None
    region_filter: Optional[str] = None
    max_recommendations: int = 5
    max_verification_rounds: int = 2
    report_format: str = "markdown"


class DataAgentOutput(BaseModel):
    """Deterministic output from Data Agent."""

    is_valid_for_analysis: bool
    dataset_profile: DatasetProfile
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    total_records: int
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None


    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class FindingType(str, Enum):
    """Categorization of analyst findings."""

    OVERALL_TREND = "overall_trend"
    PRODUCT_DECLINE = "product_decline"
    REGIONAL_PERFORMANCE = "regional_performance"
    MARGIN_ANOMALY = "margin_anomaly"
    VOLUME_AND_AOV = "volume_and_aov"


class AnalystFinding(BaseModel):
    """Individual structured analytical finding backed by deterministic numbers."""

    id: str = Field(description="Unique identifier e.g. F-01")
    finding_type: FindingType
    title: str
    metric_name: str
    computed_value: float
    prior_value: Optional[float] = None
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    time_period: str
    dimension_context: Optional[str] = None
    evidence_reference: str = Field(description="Explicit pointer to dataset computation")
    notes: Optional[str] = None


class AnalystAgentOutput(BaseModel):
    """Structured analytical results produced by Analyst Agent."""

    summary_kpis: SummaryKPIs
    period_comparison: Optional[PeriodComparison] = None
    findings: List[AnalystFinding] = Field(default_factory=list)
    trend_analysis: Optional[TrendAnalysisResult] = None
    top_products: List[ProductMetric] = Field(default_factory=list)
    declining_products: List[ProductDeclineItem] = Field(default_factory=list)
    regional_breakdown: List[RegionMetric] = Field(default_factory=list)
    category_breakdown: List[CategoryPerformance] = Field(default_factory=list)
    anomalies: List[AnomalyItem] = Field(default_factory=list)
    analytical_limitations: List[str] = Field(default_factory=list)


    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortLevel(str, Enum):
    QUICK_WIN = "quick_win"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


class Recommendation(BaseModel):
    """Structured business recommendation linked to empirical findings."""

    id: str = Field(description="Unique recommendation ID e.g. REC-01")
    title: str
    action: str = Field(description="Specific, actionable operational or commercial initiative")
    rationale: str = Field(description="Business reasoning grounded in findings")
    supporting_finding_ids: List[str] = Field(
        default_factory=list, description="IDs of empirical analyst findings that justify this"
    )
    potential_impact: ImpactLevel = ImpactLevel.HIGH
    implementation_effort: EffortLevel = EffortLevel.QUICK_WIN
    confidence_description: str = Field(description="Qualitative description of evidence strength")
    assumptions: List[str] = Field(
        default_factory=list, description="Explicit assumptions underlying this hypothesis"
    )
    suggested_follow_up: List[str] = Field(
        default_factory=list, description="Additional investigations or data required to validate"
    )


class StrategyAgentOutput(BaseModel):
    """Strategic interpretations and prioritized recommendations."""

    recommendations: List[Recommendation] = Field(default_factory=list)
    strategic_narrative: str
    identified_hypotheses: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)


    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    VERIFIED_WITH_WARNINGS = "verified_with_warnings"
    VERIFICATION_FAILED = "verification_failed"


class VerifierAgentOutput(BaseModel):
    """Structured verification results auditing numerical claims and causal validity."""

    status: VerificationStatus
    verified_findings_count: int
    failed_findings_count: int
    discrepancies: List[VerificationDiscrepancy] = Field(default_factory=list)
    unsupported_causal_claims: List[str] = Field(
        default_factory=list,
        description="Flags where correlation or temporal drop was incorrectly stated as proven causation",
    )
    inconsistencies: List[str] = Field(default_factory=list)
    verification_summary: str


    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ReportAgentOutput(BaseModel):
    """Final executive reporting output."""

    executive_summary: str
    markdown_report: str
    report_file_path: Optional[str] = None
    chart_file_paths: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    limitations_and_disclaimers: List[str] = Field(default_factory=list)


    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
