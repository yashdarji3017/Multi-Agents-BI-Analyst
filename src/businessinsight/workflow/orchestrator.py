"""Multi-Agent Orchestrator: Bounded coordination workflow for BusinessInsight AI."""

import logging
import time
from pathlib import Path
from typing import Optional

from businessinsight.config import settings
from businessinsight.workflow.schemas import AnalysisSettings, VerificationStatus
from businessinsight.workflow.state import AnalysisWorkflowState

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Coordinates the 5 specialized agents through a bounded, audited analytical workflow."""

    def __init__(self, dataset_path: Optional[Path] = None):
        from businessinsight.agents.analyst_agent import AnalystAgent
        from businessinsight.agents.data_agent import DataAgent
        from businessinsight.agents.report_agent import ReportAgent
        from businessinsight.agents.strategy_agent import StrategyAgent
        from businessinsight.agents.verifier_agent import VerifierAgent

        self.dataset_path = dataset_path or settings.dataset_path
        self.data_agent = DataAgent(self.dataset_path)
        self.analyst_agent = AnalystAgent()
        self.strategy_agent = StrategyAgent()
        self.verifier_agent = VerifierAgent()
        self.report_agent = ReportAgent()

    async def execute_analysis(
        self,
        business_question: str,
        analysis_settings: Optional[AnalysisSettings] = None,
    ) -> AnalysisWorkflowState:
        """Executes the complete multi-agent workflow end-to-end."""
        cfg = analysis_settings or AnalysisSettings()
        state = AnalysisWorkflowState(
            business_question=business_question,
            settings=cfg,
        )

        trace = state.trace
        logger.info(f"Starting MultiAgentOrchestrator analysis run [{state.analysis_id}]...")

        try:


            step1 = trace.start_step(
                agent_name="DataAgent",
                input_summary=f"Validating dataset from '{self.dataset_path}'",
            )
            data_output = await self.data_agent.run()
            state.data_output = data_output

            if not data_output.is_valid_for_analysis:
                error_msg = "; ".join(data_output.dataset_profile.quality_summary.critical_errors)
                step1.fail(f"Data validation failed: {error_msg}")
                state.status = "failed"
                state.error_message = error_msg
                trace.finalize(status="failed")
                return state

            step1.complete(
                output_summary=(
                    f"Validated {data_output.total_records:,} rows. Date range: "
                    f"{data_output.date_range_start} to {data_output.date_range_end}. "
                    f"{len(data_output.warnings)} warnings."
                ),
                input_tokens=data_output.input_tokens,
                output_tokens=data_output.output_tokens,
                metadata={"total_records": data_output.total_records},
            )
            state.status = "data_profiled"


            step2 = trace.start_step(
                agent_name="AnalystAgent",
                input_summary=f"Executing deterministic sales analytics for query: '{business_question}'",
            )
            df = self.data_agent.get_loaded_dataframe()
            analyst_output = await self.analyst_agent.run(df=df, settings=cfg)
            state.analyst_output = analyst_output

            step2.complete(
                output_summary=(
                    f"Computed {len(analyst_output.findings)} structured findings. "
                    f"Total Sales: ${analyst_output.summary_kpis.total_sales:,.2f}. "
                    f"Top declining products: {len(analyst_output.declining_products)}."
                ),
                input_tokens=analyst_output.input_tokens,
                output_tokens=analyst_output.output_tokens,
                metadata={"findings_count": len(analyst_output.findings)},
            )
            state.status = "analyzed"


            step3 = trace.start_step(
                agent_name="StrategyAgent",
                input_summary=f"Synthesizing recommendations for {len(analyst_output.findings)} empirical findings",
            )
            strategy_output = await self.strategy_agent.run(
                analyst_output=analyst_output,
                business_question=business_question,
                max_recommendations=cfg.max_recommendations,
            )
            state.strategy_output = strategy_output

            step3.complete(
                output_summary=f"Formulated {len(strategy_output.recommendations)} evidence-linked recommendations.",
                input_tokens=strategy_output.input_tokens,
                output_tokens=strategy_output.output_tokens,
                metadata={"recommendations_count": len(strategy_output.recommendations)},
            )
            state.status = "strategized"


            step4 = trace.start_step(
                agent_name="VerifierAgent",
                input_summary="Auditing numerical claims and checking for unsupported causal leaps",
            )


            verifier_output = None
            max_rounds = min(cfg.max_verification_rounds, 3)

            for round_idx in range(1, max_rounds + 1):
                state.verification_round = round_idx
                verifier_output = await self.verifier_agent.run(
                    analyst_output=analyst_output,
                    strategy_output=strategy_output,
                )


                if verifier_output.status != VerificationStatus.VERIFICATION_FAILED:
                    break
                else:
                    logger.warning(
                        f"Verification round {round_idx} identified issues: {verifier_output.discrepancies}. Re-evaluating."
                    )

            state.verifier_output = verifier_output
            step4.complete(
                output_summary=(
                    f"Audit status: {verifier_output.status.value.upper()}. "
                    f"Verified {verifier_output.verified_findings_count} findings. "
                    f"{len(verifier_output.discrepancies)} discrepancies. "
                    f"{len(verifier_output.unsupported_causal_claims)} causal warnings."
                ),
                input_tokens=verifier_output.input_tokens,
                output_tokens=verifier_output.output_tokens,
                metadata={
                    "verification_status": verifier_output.status.value,
                    "verified_count": verifier_output.verified_findings_count,
                },
            )
            state.status = "verified"


            step5 = trace.start_step(
                agent_name="ReportAgent",
                input_summary="Synthesizing verified findings into executive Markdown report",
            )
            report_output = await self.report_agent.run(
                analysis_id=state.analysis_id,
                business_question=business_question,
                data_output=data_output,
                analyst_output=analyst_output,
                strategy_output=strategy_output,
                verifier_output=verifier_output,
            )
            state.report_output = report_output

            step5.complete(
                output_summary=f"Generated executive report. Path: {report_output.report_file_path or 'In-memory'}",
                input_tokens=report_output.input_tokens,
                output_tokens=report_output.output_tokens,
                metadata={"report_path": report_output.report_file_path},
            )
            state.status = "completed"
            state.completed_at = time.time()
            trace.finalize(status="completed")

        except Exception as e:
            logger.exception(f"Unhandled error in workflow orchestrator: {e}")
            state.status = "failed"
            state.error_message = str(e)
            trace.finalize(status="failed")

        return state
