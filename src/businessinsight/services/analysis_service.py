"""Analysis Service: In-memory orchestrator coordination and session history store.

NOTE: Per architecture specifications, NO database is used. All session history is kept
in memory for the duration of the active process and is cleared on application restart.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd

from businessinsight.analytics import (
    analyze_monthly_trend,
    analyze_product_performance,
    analyze_quarterly_trend,
    analyze_regional_performance,
    calculate_kpis,
    compare_periods,
    detect_anomalies,
    profile_dataset,
)
from businessinsight.api.schemas import DatasetAnalyticsResponse
from businessinsight.data.loader import DataLoader
from businessinsight.data.validators import DatasetProfile
from businessinsight.observability.tracing import AgentExecutionTrace
from businessinsight.reporting.charts import export_charts_for_analysis
from businessinsight.workflow.orchestrator import MultiAgentOrchestrator
from businessinsight.workflow.schemas import AnalysisSettings, ReportAgentOutput
from businessinsight.workflow.state import AnalysisWorkflowState

logger = logging.getLogger(__name__)


class AnalysisService:
    """Manages active session multi-agent analysis runs and in-memory history cache."""

    def __init__(self):

        self._history: Dict[str, AnalysisWorkflowState] = {}

        self._charts_cache: Dict[str, Dict[str, str]] = {}
        self._cached_profile: Optional[DatasetProfile] = None

    def get_dataset_profile(self, force_refresh: bool = False) -> DatasetProfile:
        """Inspects and profiles the configured dataset."""
        if self._cached_profile is None or force_refresh:
            self._cached_profile = profile_dataset()
        return self._cached_profile

    def get_dataset_analytics(
        self,
        category: Optional[str] = None,
        region: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        comparison_mode: str = "latest_vs_previous_quarter",
    ) -> DatasetAnalyticsResponse:
        """Computes comprehensive analytical slice without triggering LLM agents."""
        loader = DataLoader()
        df, _ = loader.load_canonical()

        avail_categories = sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else []
        avail_regions = sorted(df["region"].dropna().unique().tolist()) if "region" in df.columns else []
        min_d = df["order_date"].min().strftime("%Y-%m-%d") if "order_date" in df.columns else None
        max_d = df["order_date"].max().strftime("%Y-%m-%d") if "order_date" in df.columns else None

        filtered_df = df.copy()
        if category and category != "All Categories" and "category" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["category"] == category]
        if region and region != "All Regions" and "region" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["region"] == region]
        if start_date and "order_date" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["order_date"] >= pd.to_datetime(start_date)]
        if end_date and "order_date" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["order_date"] <= pd.to_datetime(end_date)]

        kpis = calculate_kpis(filtered_df)
        monthly = analyze_monthly_trend(filtered_df)
        quarterly = analyze_quarterly_trend(filtered_df)

        period_comp = None
        df_curr = pd.DataFrame()
        df_prior = pd.DataFrame()

        if (
            comparison_mode == "latest_vs_previous_quarter"
            and quarterly.data_points
            and len(quarterly.data_points) >= 2
        ):
            latest_q = quarterly.latest_complete_period
            prev_q = quarterly.previous_complete_period
            df_curr = filtered_df[filtered_df["quarter"] == latest_q]
            df_prior = filtered_df[filtered_df["quarter"] == prev_q]
            period_comp = compare_periods(df_prior, df_curr, prior_label=prev_q, current_label=latest_q)
        elif (
            comparison_mode == "latest_vs_previous_month"
            and monthly.data_points
            and len(monthly.data_points) >= 2
        ):
            latest_m = monthly.latest_complete_period
            prev_m = monthly.previous_complete_period
            df_curr = filtered_df[filtered_df["year_month"] == latest_m]
            df_prior = filtered_df[filtered_df["year_month"] == prev_m]
            period_comp = compare_periods(df_prior, df_curr, prior_label=prev_m, current_label=latest_m)
        elif len(filtered_df) >= 2:
            sorted_df = filtered_df.sort_values("order_date")
            half = len(sorted_df) // 2
            df_prior = sorted_df.iloc[:half]
            df_curr = sorted_df.iloc[half:]
            period_comp = compare_periods(df_prior, df_curr, prior_label="H1 Historical", current_label="H2 Recent")

        prods = analyze_product_performance(
            df_current=df_curr if not df_curr.empty else filtered_df,
            df_prior=df_prior if not df_prior.empty else None,
            top_n=10,
        )
        regs = analyze_regional_performance(
            df_current=df_curr if not df_curr.empty else filtered_df,
            df_prior=df_prior if not df_prior.empty else None,
        )
        anomalies = detect_anomalies(filtered_df)

        return DatasetAnalyticsResponse(
            kpis=kpis,
            monthly_trend=monthly,
            quarterly_trend=quarterly,
            period_comparison=period_comp,
            top_products=prods.top_products_by_sales,
            declining_products=prods.declining_products,
            category_breakdown=prods.category_breakdown,
            regional_breakdown=regs.regions,
            anomalies=anomalies,
            available_categories=avail_categories,
            available_regions=avail_regions,
            min_date=min_d,
            max_date=max_d,
        )

    async def run_analysis(
        self,
        business_question: str,
        settings: Optional[AnalysisSettings] = None,
    ) -> AnalysisWorkflowState:
        """Executes a multi-agent analysis workflow and retains result in memory."""
        orchestrator = MultiAgentOrchestrator()
        state = await orchestrator.execute_analysis(
            business_question=business_question,
            analysis_settings=settings,
        )


        self._history[state.analysis_id] = state


        if state.status == "completed" and state.analyst_output:
            try:
                chart_paths = export_charts_for_analysis(
                    analyst_output=state.analyst_output,
                    analysis_id=state.analysis_id,
                )
                self._charts_cache[state.analysis_id] = chart_paths
            except Exception as e:
                logger.warning(f"Failed to export local chart artifacts: {e}")

        return state

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisWorkflowState]:
        """Retrieves an analysis run by ID from in-memory session cache."""
        return self._history.get(analysis_id)

    def get_trace(self, analysis_id: str) -> Optional[AgentExecutionTrace]:
        """Retrieves execution trace for an analysis run."""
        state = self.get_analysis(analysis_id)
        return state.trace if state else None

    def get_report(self, analysis_id: str) -> Optional[ReportAgentOutput]:
        """Retrieves generated executive report for an analysis run."""
        state = self.get_analysis(analysis_id)
        return state.report_output if state else None

    def get_charts(self, analysis_id: str) -> Dict[str, str]:
        """Retrieves chart file paths for an analysis run."""
        return self._charts_cache.get(analysis_id, {})

    def list_recent_analyses(self) -> List[Dict[str, str]]:
        """Lists recent analyses from current session memory."""
        results = []
        for aid, state in self._history.items():
            results.append(
                {
                    "analysis_id": aid,
                    "business_question": state.business_question,
                    "status": state.status,
                    "created_at": str(state.created_at),
                }
            )
        return results


analysis_service = AnalysisService()
