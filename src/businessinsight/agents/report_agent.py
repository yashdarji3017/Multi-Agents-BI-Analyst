"""Report Agent: Assembles verified analytical findings into executive Markdown reports."""

import logging
from pathlib import Path
from typing import Optional
from businessinsight.agents.base import count_gemini_tokens, extract_token_usage, get_gemini_agent
from businessinsight.config import settings
from businessinsight.workflow.schemas import (
    AnalystAgentOutput,
    DataAgentOutput,
    ReportAgentOutput,
    StrategyAgentOutput,
    VerifierAgentOutput,
)

logger = logging.getLogger(__name__)

REPORT_AGENT_INSTRUCTIONS = """You are the Executive Report Agent in BusinessInsight AI.
Your role is to author polished, C-suite ready executive Markdown reports summarizing business performance.
REPORTING PRINCIPLES:
1. Ground every single dollar figure, order count, and growth percentage directly in the verified findings.
2. Present tables and breakdowns clearly.
3. Separate empirical findings from hypotheses and future strategic recommendations.
4. Highlight data limitations and verification audit outcomes."""


class ReportAgent:
    """Agent 5: Generates verified C-suite business intelligence reports."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.report_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._maf_agent = get_gemini_agent(
            name="ReportAgent",
            instructions=REPORT_AGENT_INSTRUCTIONS,
        )

    async def run(
        self,
        analysis_id: str,
        business_question: str,
        data_output: DataAgentOutput,
        analyst_output: AnalystAgentOutput,
        strategy_output: StrategyAgentOutput,
        verifier_output: VerifierAgentOutput,
    ) -> ReportAgentOutput:
        """Assembles verified analytical outputs into a comprehensive executive report."""
        logger.info(f"ReportAgent: Assembling executive report for analysis {analysis_id}...")

        kpis = analyst_output.summary_kpis
        period_comp = analyst_output.period_comparison


        exec_summary = (
            f"This business intelligence report investigates the question: **'{business_question}'**.\n\n"
            f"Over the evaluated period ({kpis.date_start} to {kpis.date_end}), cumulative revenue reached "
            f"**${kpis.total_sales:,.2f}** across **{kpis.distinct_orders:,}** distinct orders, yielding an "
            f"Average Order Value (AOV) of **${kpis.average_order_value:,.2f}**.\n\n"
        )

        if period_comp:
            pct_text = (
                f"{period_comp.percentage_sales_change:+.2f}%"
                if period_comp.percentage_sales_change is not None
                else "N/A"
            )
            exec_summary += (
                f"Comparing **{period_comp.current_period_label}** against **{period_comp.prior_period_label}**, "
                f"sales shifted by **${period_comp.absolute_sales_change:+,.2f}** ({pct_text}). "
                f"Independent verification status: **{verifier_output.status.value.upper()}** "
                f"({verifier_output.verified_findings_count} findings mathematically audited)."
            )


        md_lines = []
        md_lines.append(f"# Executive Business Intelligence Report")
        md_lines.append(f"**Analysis Reference ID:** `{analysis_id}`  ")
        md_lines.append(f"**Business Query:** *{business_question}*  ")
        md_lines.append(f"**Verification Status:** `{verifier_output.status.value.upper()}`  \n")

        md_lines.append("## 1. Executive Summary")
        md_lines.append(exec_summary)
        md_lines.append("")

        md_lines.append("## 2. Key Performance Indicators")
        md_lines.append("| Metric | Value | Context |")
        md_lines.append("|---|---|---|")
        md_lines.append(f"| **Total Sales** | `${kpis.total_sales:,.2f}` | Cumulative across dataset slice |")
        md_lines.append(f"| **Distinct Orders** | `{kpis.distinct_orders:,}` | De-duplicated order volume |")
        md_lines.append(f"| **Units Sold** | `{kpis.total_units_sold:,}` | Total items fulfilled |")
        md_lines.append(f"| **Average Order Value (AOV)** | `${kpis.average_order_value:,.2f}` | Revenue per distinct order |")
        if kpis.total_profit is not None:
            md_lines.append(f"| **Net Profit** | `${kpis.total_profit:,.2f}` | Reported transaction profit |")
            md_lines.append(f"| **Profit Margin** | `{kpis.profit_margin_pct or 0.0:.2f}%` | Net profit / sales revenue |")
        if kpis.average_discount_pct is not None:
            md_lines.append(f"| **Average Discount** | `{kpis.average_discount_pct:.1f}%` | Mean transaction discount |")
        md_lines.append("")

        if period_comp:
            md_lines.append("## 3. Period-over-Period Performance Comparison")
            md_lines.append(f"Comparing **{period_comp.prior_period_label}** vs. **{period_comp.current_period_label}**:\n")
            md_lines.append("| Metric | Prior Period | Current Period | Absolute Change | Percentage Change |")
            md_lines.append("|---|---|---|---|---|")
            pct_s = f"{period_comp.percentage_sales_change:+.2f}%" if period_comp.percentage_sales_change is not None else "N/A"
            md_lines.append(
                f"| **Sales Revenue** | `${period_comp.prior_sales:,.2f}` | `${period_comp.current_sales:,.2f}` | "
                f"`${period_comp.absolute_sales_change:+,.2f}` | `{pct_s}` |"
            )
            pct_o = f"{period_comp.percentage_order_change:+.2f}%" if period_comp.percentage_order_change is not None else "N/A"
            md_lines.append(
                f"| **Distinct Orders** | `{period_comp.prior_orders:,}` | `{period_comp.current_orders:,}` | "
                f"`{period_comp.absolute_order_change:+d}` | `{pct_o}` |"
            )
            pct_aov = f"{period_comp.percentage_aov_change:+.2f}%" if period_comp.percentage_aov_change is not None else "N/A"
            md_lines.append(
                f"| **Average Order Value** | `${period_comp.prior_aov:,.2f}` | `${period_comp.current_aov:,.2f}` | "
                f"`${period_comp.absolute_aov_change:+,.2f}` | `{pct_aov}` |"
            )
            if period_comp.prior_profit is not None and period_comp.current_profit is not None:
                md_lines.append(
                    f"| **Net Profit** | `${period_comp.prior_profit:,.2f}` | `${period_comp.current_profit:,.2f}` | "
                    f"`${period_comp.absolute_profit_change:+,.2f}` | - |"
                )
            md_lines.append("")


        if analyst_output.regional_breakdown:
            md_lines.append("## 4. Regional Performance Breakdown")
            md_lines.append("| Region | Revenue | Share (%) | Orders | Units | Profit | Margin (%) |")
            md_lines.append("|---|---|---|---|---|---|---|")
            for reg in analyst_output.regional_breakdown:
                md_lines.append(
                    f"| **{reg.region}** | `${reg.sales:,.2f}` | `{reg.sales_share_pct:.1f}%` | "
                    f"`{reg.orders:,}` | `{reg.units:,}` | `${reg.profit:,.2f}` | `{reg.profit_margin_pct:.1f}%` |"
                )
            md_lines.append("")


        if analyst_output.declining_products:
            md_lines.append("## 5. Products with Largest Absolute Revenue Decline")
            md_lines.append("| Product Name | Category | Prior Sales | Current Sales | Absolute Decline | Contrib to Decline (%) |")
            md_lines.append("|---|---|---|---|---|---|")
            for p in analyst_output.declining_products[:5]:
                md_lines.append(
                    f"| {p.product_name[:35]}... | {p.category} | `${p.prior_sales:,.2f}` | `${p.current_sales:,.2f}` | "
                    f"`${p.absolute_sales_change:,.2f}` | `{p.contribution_to_total_decline_pct or 0.0:.1f}%` |"
                )
            md_lines.append("")


        md_lines.append("## 6. Empirical Findings & Independent Verification Audit")
        md_lines.append(f"> **Verification Note:** {verifier_output.verification_summary}\n")
        for f in analyst_output.findings:
            md_lines.append(f"### Finding {f.id}: {f.title}")
            md_lines.append(f"- **Metric:** `{f.metric_name}` | **Observed Value:** `{f.computed_value:,.2f}`")
            md_lines.append(f"- **Evidence Reference:** {f.evidence_reference}")
            if f.notes:
                md_lines.append(f"- **Analysis:** {f.notes}")
            md_lines.append("")

        if verifier_output.unsupported_causal_claims:
            md_lines.append("### Causal Validity Warnings")
            for claim in verifier_output.unsupported_causal_claims:
                md_lines.append(f"- ⚠️ {claim}")
            md_lines.append("")


        md_lines.append("## 7. Evidence-Backed Strategic Recommendations")
        md_lines.append(f"*{strategy_output.strategic_narrative}*\n")
        for rec in strategy_output.recommendations:
            md_lines.append(f"### {rec.id}: {rec.title}")
            md_lines.append(f"- **Recommended Action:** {rec.action}")
            md_lines.append(f"- **Business Rationale:** {rec.rationale}")
            md_lines.append(f"- **Impact Level:** `{rec.potential_impact.value.upper()}` | **Effort:** `{rec.implementation_effort.value.upper()}`")
            md_lines.append(f"- **Linked Findings:** {', '.join(rec.supporting_finding_ids) if rec.supporting_finding_ids else 'General'}")
            if rec.assumptions:
                md_lines.append(f"- **Underlying Assumptions:** {'; '.join(rec.assumptions)}")
            if rec.suggested_follow_up:
                md_lines.append(f"- **Required Validation Data:** {'; '.join(rec.suggested_follow_up)}")
            md_lines.append("")


        md_lines.append("## 8. Data Quality Indicators & Limitations")
        for warn in data_output.warnings:
            md_lines.append(f"- **Quality Indicator:** {warn}")
        for lim in analyst_output.analytical_limitations:
            md_lines.append(f"- **Analytical Limitation:** {lim}")
        md_lines.append("")


        rep_in_tokens = count_gemini_tokens(exec_summary)

        rep_out_tokens = count_gemini_tokens("\n".join(md_lines))

        md_lines.append("## 9. Token Economics Audit (Gemini Inbuilt Tokenizer)")
        md_lines.append("| Agent Name | Input Tokens | Output Tokens | Total Tokens |")
        md_lines.append("|---|---|---|---|")
        md_lines.append(f"| **Data Agent** | `{data_output.input_tokens:,}` | `{data_output.output_tokens:,}` | `{data_output.total_tokens:,}` |")
        md_lines.append(f"| **Analyst Agent** | `{analyst_output.input_tokens:,}` | `{analyst_output.output_tokens:,}` | `{analyst_output.total_tokens:,}` |")
        md_lines.append(f"| **Strategy Agent** | `{strategy_output.input_tokens:,}` | `{strategy_output.output_tokens:,}` | `{strategy_output.total_tokens:,}` |")
        md_lines.append(f"| **Verifier Agent** | `{verifier_output.input_tokens:,}` | `{verifier_output.output_tokens:,}` | `{verifier_output.total_tokens:,}` |")
        md_lines.append(f"| **Report Agent** | `{rep_in_tokens:,}` | `{rep_out_tokens:,}` | `{rep_in_tokens + rep_out_tokens:,}` |")
        total_all_tokens = (
            data_output.total_tokens
            + analyst_output.total_tokens
            + strategy_output.total_tokens
            + verifier_output.total_tokens
            + (rep_in_tokens + rep_out_tokens)
        )
        md_lines.append(f"| **Total Pipeline** | - | - | **`{total_all_tokens:,}`** |")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("*Generated autonomously by BusinessInsight AI Multi-Agent System.*")

        full_markdown = "\n".join(md_lines)


        report_filename = f"report_{analysis_id[:8]}.md"
        report_file_path = self.output_dir / report_filename
        try:
            with open(report_file_path, "w", encoding="utf-8") as f:
                f.write(full_markdown)
            saved_path_str = str(report_file_path)
        except Exception as e:
            logger.error(f"Failed to write report file to disk: {e}")
            saved_path_str = None

        key_takeaways = [
            f"Cumulative revenue reached ${kpis.total_sales:,.2f} with an AOV of ${kpis.average_order_value:,.2f}.",
            f"{len(strategy_output.recommendations)} evidence-backed recommendations prioritized for commercial action.",
            f"Audit verification completed with status: {verifier_output.status.value.upper()}.",
            f"Total Gemini native tokens utilized across agents: {total_all_tokens:,}.",
        ]

        return ReportAgentOutput(
            executive_summary=exec_summary,
            markdown_report=full_markdown,
            report_file_path=saved_path_str,
            key_takeaways=key_takeaways,
            limitations_and_disclaimers=analyst_output.analytical_limitations,
            input_tokens=rep_in_tokens,
            output_tokens=rep_out_tokens,
            total_tokens=rep_in_tokens + rep_out_tokens,
        )
