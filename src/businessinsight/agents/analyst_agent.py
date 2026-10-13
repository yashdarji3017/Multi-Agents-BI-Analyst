"""Analyst Agent: Performs deterministic calculations and structures empirical findings."""

import logging
from typing import List, Optional
import pandas as pd

from businessinsight.agents.base import extract_token_usage, get_gemini_agent
from businessinsight.analytics import (
    analyze_monthly_trend,
    analyze_product_performance,
    analyze_quarterly_trend,
    analyze_regional_performance,
    calculate_kpis,
    compare_periods,
    detect_anomalies,
)
from businessinsight.workflow.schemas import (
    AnalysisSettings,
    AnalystAgentOutput,
    AnalystFinding,
    ComparisonMode,
    FindingType,
)

logger = logging.getLogger(__name__)

ANALYST_AGENT_INSTRUCTIONS = """You are the Senior Analyst Agent in BusinessInsight AI.
Your responsibility is to analyze the empirical financial findings computed by our deterministic Python analytics engine.
Synthesize the observations into structured findings, explaining trends, regional performance shifts, and top declining products.
CRITICAL MANDATE:
- Never calculate, estimate, or invent numerical values.
- All numbers must come strictly from the provided deterministic calculations.
- Always distinguish between absolute dollar changes and percentage growth rates.
- Link all assertions to explicit metric definitions and computed evidence."""


class AnalystAgent:
    """Agent 2: Executes deterministic analytics and synthesizes structured findings."""

    def __init__(self):
        self._maf_agent = get_gemini_agent(
            name="AnalystAgent",
            instructions=ANALYST_AGENT_INSTRUCTIONS,
        )

    async def run(self, df: pd.DataFrame, settings: AnalysisSettings) -> AnalystAgentOutput:
        """Executes analytical engine over dataset slices and structures findings."""
        logger.info("AnalystAgent: Running deterministic analytics...")


        filtered_df = df.copy()
        if settings.product_category_filter and "category" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["category"] == settings.product_category_filter]
        if settings.region_filter and "region" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["region"] == settings.region_filter]
        if settings.start_date and "order_date" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["order_date"] >= pd.to_datetime(settings.start_date)]
        if settings.end_date and "order_date" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["order_date"] <= pd.to_datetime(settings.end_date)]


        summary_kpis = calculate_kpis(filtered_df)


        monthly_trend = analyze_monthly_trend(filtered_df)
        quarterly_trend = analyze_quarterly_trend(filtered_df)


        period_comparison = None
        df_curr = pd.DataFrame()
        df_prior = pd.DataFrame()

        if settings.comparison_mode == ComparisonMode.LATEST_VS_PREVIOUS_QUARTER:
            if quarterly_trend.data_points and len(quarterly_trend.data_points) >= 2:
                latest_q = quarterly_trend.latest_complete_period
                prev_q = quarterly_trend.previous_complete_period
                df_curr = filtered_df[filtered_df["quarter"] == latest_q]
                df_prior = filtered_df[filtered_df["quarter"] == prev_q]
                period_comparison = compare_periods(df_prior, df_curr, prior_label=prev_q, current_label=latest_q)
        elif settings.comparison_mode == ComparisonMode.LATEST_VS_PREVIOUS_MONTH:
            if monthly_trend.data_points and len(monthly_trend.data_points) >= 2:
                latest_m = monthly_trend.latest_complete_period
                prev_m = monthly_trend.previous_complete_period
                df_curr = filtered_df[filtered_df["year_month"] == latest_m]
                df_prior = filtered_df[filtered_df["year_month"] == prev_m]
                period_comparison = compare_periods(df_prior, df_curr, prior_label=prev_m, current_label=latest_m)


        if period_comparison is None:

            if len(filtered_df) >= 2:
                sorted_df = filtered_df.sort_values("order_date")
                half = len(sorted_df) // 2
                df_prior = sorted_df.iloc[:half]
                df_curr = sorted_df.iloc[half:]
                period_comparison = compare_periods(
                    df_prior, df_curr, prior_label="H1 Historical", current_label="H2 Recent"
                )


        product_results = analyze_product_performance(
            df_current=df_curr if not df_curr.empty else filtered_df,
            df_prior=df_prior if not df_prior.empty else None,
            top_n=10,
        )


        regional_results = analyze_regional_performance(
            df_current=df_curr if not df_curr.empty else filtered_df,
            df_prior=df_prior if not df_prior.empty else None,
        )


        anomalies = detect_anomalies(filtered_df)


        findings: List[AnalystFinding] = []
        finding_counter = 1

        if period_comparison:

            pct_str = (
                f"{period_comparison.percentage_sales_change:+.2f}%"
                if period_comparison.percentage_sales_change is not None
                else "N/A"
            )
            findings.append(
                AnalystFinding(
                    id=f"F-{finding_counter:02d}",
                    finding_type=FindingType.OVERALL_TREND,
                    title=f"Sales Revenue Shift ({period_comparison.prior_period_label} to {period_comparison.current_period_label})",
                    metric_name="total_sales",
                    computed_value=period_comparison.current_sales,
                    prior_value=period_comparison.prior_sales,
                    absolute_change=period_comparison.absolute_sales_change,
                    percentage_change=period_comparison.percentage_sales_change,
                    time_period=f"{period_comparison.prior_period_label} vs {period_comparison.current_period_label}",
                    evidence_reference=f"Calculated from {len(df_curr)} current records vs {len(df_prior)} prior records",
                    notes=f"Revenue changed by ${period_comparison.absolute_sales_change:+,.2f} ({pct_str}).",
                )
            )
            finding_counter += 1


            findings.append(
                AnalystFinding(
                    id=f"F-{finding_counter:02d}",
                    finding_type=FindingType.VOLUME_AND_AOV,
                    title="Order Volume and Average Order Value Dynamics",
                    metric_name="average_order_value",
                    computed_value=period_comparison.current_aov,
                    prior_value=period_comparison.prior_aov,
                    absolute_change=period_comparison.absolute_aov_change,
                    percentage_change=period_comparison.percentage_aov_change,
                    time_period=f"{period_comparison.prior_period_label} vs {period_comparison.current_period_label}",
                    evidence_reference=f"Orders: {period_comparison.prior_orders} -> {period_comparison.current_orders}",
                    notes=(
                        f"Distinct order volume changed by {period_comparison.absolute_order_change:+d} orders. "
                        f"AOV shifted from ${period_comparison.prior_aov:,.2f} to ${period_comparison.current_aov:,.2f}."
                    ),
                )
            )
            finding_counter += 1


        if product_results.declining_products:
            top_decline = product_results.declining_products[0]
            findings.append(
                AnalystFinding(
                    id=f"F-{finding_counter:02d}",
                    finding_type=FindingType.PRODUCT_DECLINE,
                    title=f"Largest Product Revenue Contraction: {top_decline.product_name[:40]}",
                    metric_name="product_revenue_decline",
                    computed_value=top_decline.current_sales,
                    prior_value=top_decline.prior_sales,
                    absolute_change=top_decline.absolute_sales_change,
                    percentage_change=top_decline.percentage_sales_change,
                    time_period=period_comparison.current_period_label if period_comparison else "Current Period",
                    dimension_context=top_decline.category,
                    evidence_reference=(
                        f"Product Sales dropped from ${top_decline.prior_sales:,.2f} to ${top_decline.current_sales:,.2f} "
                        f"(Units: {top_decline.prior_units} -> {top_decline.current_units})."
                    ),
                    notes=f"Contributed {top_decline.contribution_to_total_decline_pct or 0.0:.1f}% of total declining product pool.",
                )
            )
            finding_counter += 1


        if regional_results.top_declining_region:
            declining_reg_match = next(
                (r for r in regional_results.regions if r.region == regional_results.top_declining_region),
                None,
            )
            if declining_reg_match and declining_reg_match.absolute_sales_change is not None:
                findings.append(
                    AnalystFinding(
                        id=f"F-{finding_counter:02d}",
                        finding_type=FindingType.REGIONAL_PERFORMANCE,
                        title=f"Regional Contraction in {declining_reg_match.region}",
                        metric_name="regional_sales_decline",
                        computed_value=declining_reg_match.sales,
                        prior_value=declining_reg_match.prior_sales,
                        absolute_change=declining_reg_match.absolute_sales_change,
                        percentage_change=declining_reg_match.percentage_sales_change,
                        time_period=period_comparison.current_period_label if period_comparison else "Current Period",
                        dimension_context=declining_reg_match.region,
                        evidence_reference=f"Regional revenue shifted by ${declining_reg_match.absolute_sales_change:+,.2f}",
                        notes=f"Regional share: {declining_reg_match.sales_share_pct:.1f}% of total revenue.",
                    )
                )
                finding_counter += 1


        margin_anomalies = [a for a in anomalies if a.anomaly_type == "severe_negative_profit"]
        if margin_anomalies:
            first_loss = margin_anomalies[0]
            findings.append(
                AnalystFinding(
                    id=f"F-{finding_counter:02d}",
                    finding_type=FindingType.MARGIN_ANOMALY,
                    title="Severe Negative Margin Transactions Detected",
                    metric_name="negative_profit_transaction",
                    computed_value=first_loss.metric_value,
                    time_period="Observed Period",
                    evidence_reference=first_loss.description,
                    notes="Deep discounts correlated with substantial negative bottom-line profit.",
                )
            )

        limitations = [
            "Revenue figures reflect transaction-level invoiced sales and do not capture post-period returns or bad debt.",
            "AOV is computed on unique Order IDs, which may bundle disparate category line items.",
        ]

        input_tokens = 0
        output_tokens = 0


        if self._maf_agent is not None:
            try:

                full_csv_data = filtered_df.to_csv(index=False)


                prompt = (
                    f"Here is the complete sales transaction dataset ({len(filtered_df)} records):\n\n"
                    f"{full_csv_data}\n\n"
                    f"Analyze all transactions, explain sales trends, and summarize top declining products."
                )
                resp = await self._maf_agent.run(prompt)
                input_tokens, output_tokens = extract_token_usage(resp, prompt_text=prompt)
                if resp and hasattr(resp, "text") and resp.text:
                    limitations.append(f"Analyst Perspective: {resp.text.strip()}")
            except Exception as e:
                logger.warning(f"AnalystAgent LLM call skipped: {e}")

        return AnalystAgentOutput(
            summary_kpis=summary_kpis,
            period_comparison=period_comparison,
            findings=findings,
            trend_analysis=quarterly_trend,
            top_products=product_results.top_products_by_sales,
            declining_products=product_results.declining_products,
            regional_breakdown=regional_results.regions,
            category_breakdown=product_results.category_breakdown,
            anomalies=anomalies,
            analytical_limitations=limitations,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
