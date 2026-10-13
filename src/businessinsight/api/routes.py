"""FastAPI REST routing definitions."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from businessinsight.agents.base import is_maf_gemini_ready
from businessinsight.api.schemas import (
    AnalysisSummaryResponse,
    DatasetAnalyticsResponse,
    HealthResponse,
    RunAnalysisRequest,
)
from businessinsight.config import settings
from businessinsight.data.validators import DatasetProfile
from businessinsight.observability.tracing import AgentExecutionTrace
from businessinsight.services.analysis_service import analysis_service
from businessinsight.workflow.schemas import ReportAgentOutput
from businessinsight.workflow.state import AnalysisWorkflowState

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health and Runtime Architecture Status",
)
def get_health() -> HealthResponse:
    """Checks service health, dataset file status, and confirms no database is active."""
    return HealthResponse(
        status="healthy",
        service="BusinessInsight AI",
        version="0.1.0",
        database="None (In-Memory Processing)",
        dataset_configured=bool(settings.dataset_path),
        dataset_exists=settings.dataset_path.exists(),
        maf_gemini_ready=is_maf_gemini_ready(),
    )


@router.get(
    "/dataset/profile",
    response_model=DatasetProfile,
    summary="Inspect and Profile Configured Sales Dataset",
)
def get_dataset_profile() -> DatasetProfile:
    """Profiles the sales dataset and returns column mappings and quality indicators."""
    try:
        return analysis_service.get_dataset_profile()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to profile dataset: {e}",
        )


@router.get(
    "/dataset/analytics",
    response_model=DatasetAnalyticsResponse,
    summary="Compute Slice Analytics for Interactive Visualizations",
)
def get_dataset_analytics(
    category: Optional[str] = Query(default=None, description="Product category filter"),
    region: Optional[str] = Query(default=None, description="Territory filter"),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    comparison_mode: str = Query(
        default="latest_vs_previous_quarter", description="Temporal comparison interval"
    ),
) -> DatasetAnalyticsResponse:
    """Computes KPIs, trends, product contractions, and regional distributions for dashboard views."""
    try:
        return analysis_service.get_dataset_analytics(
            category=category,
            region=region,
            start_date=start_date,
            end_date=end_date,
            comparison_mode=comparison_mode,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Analytics calculation failed: {e}"
        )


@router.post(
    "/analysis/run",
    response_model=AnalysisSummaryResponse,
    summary="Execute Multi-Agent Business Intelligence Analysis",
)
async def run_analysis(request: RunAnalysisRequest) -> AnalysisSummaryResponse:
    """Triggers the bounded 5-agent workflow for a given business question."""
    if not request.business_question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Business question must not be empty.",
        )

    try:
        state = await analysis_service.run_analysis(
            business_question=request.business_question,
            settings=request.settings,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    if state.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis failed: {state.error_message}",
        )

    total_sales = (
        state.analyst_output.summary_kpis.total_sales if state.analyst_output else None
    )
    findings_count = len(state.analyst_output.findings) if state.analyst_output else 0
    recs_count = (
        len(state.strategy_output.recommendations) if state.strategy_output else 0
    )
    exec_summary = (
        state.report_output.executive_summary if state.report_output else None
    )
    verif_status = (
        state.verifier_output.status.value if state.verifier_output else None
    )

    return AnalysisSummaryResponse(
        analysis_id=state.analysis_id,
        business_question=state.business_question,
        status=state.status,
        duration_seconds=state.trace.total_duration_seconds,
        verification_status=verif_status,
        executive_summary=exec_summary,
        total_sales=total_sales,
        findings_count=findings_count,
        recommendations_count=recs_count,
        total_input_tokens=state.trace.total_input_tokens,
        total_output_tokens=state.trace.total_output_tokens,
        total_tokens=state.trace.total_tokens,
        token_usage_by_agent=state.trace.token_usage_by_agent,
    )


@router.get(
    "/analysis",
    response_model=List[Dict[str, str]],
    summary="List In-Memory Analyses for Active Session",
)
def list_analyses() -> List[Dict[str, str]]:
    """Lists current session analyses held in memory."""
    return analysis_service.list_recent_analyses()


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisWorkflowState,
    summary="Get Full Multi-Agent Analysis State",
)
def get_analysis_by_id(analysis_id: str) -> AnalysisWorkflowState:
    """Retrieves full workflow state from in-memory session cache."""
    state = analysis_service.get_analysis(analysis_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Analysis ID '{analysis_id}' not found in active session memory. "
                "Note: History is kept in memory only and is cleared when the process restarts."
            ),
        )
    return state


@router.get(
    "/analysis/{analysis_id}/trace",
    response_model=AgentExecutionTrace,
    summary="Get Agent Execution Trace and Step Latencies",
)
def get_analysis_trace(analysis_id: str) -> AgentExecutionTrace:
    """Retrieves the step-by-step agent execution trace."""
    trace = analysis_service.get_trace(analysis_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution trace for '{analysis_id}' not found in session memory.",
        )
    return trace


@router.get(
    "/analysis/{analysis_id}/report",
    response_model=ReportAgentOutput,
    summary="Get Verified Executive Markdown Report",
)
def get_analysis_report(analysis_id: str) -> ReportAgentOutput:
    """Retrieves generated executive report schema."""
    report = analysis_service.get_report(analysis_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for '{analysis_id}' not found in session memory.",
        )
    return report


@router.get(
    "/analysis/{analysis_id}/report/raw",
    response_class=PlainTextResponse,
    summary="Download Raw Markdown Document",
)
def get_raw_markdown_report(analysis_id: str) -> str:
    """Returns raw Markdown text of the generated report."""
    report = analysis_service.get_report(analysis_id)
    if not report or not report.markdown_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Markdown report for '{analysis_id}' not found.",
        )
    return report.markdown_report


@router.get(
    "/analysis/{analysis_id}/charts",
    response_model=Dict[str, str],
    summary="Get Generated Plotly Chart Artifact File Paths",
)
def get_analysis_charts(analysis_id: str) -> Dict[str, str]:
    """Retrieves local paths for generated chart artifacts."""
    return analysis_service.get_charts(analysis_id)
