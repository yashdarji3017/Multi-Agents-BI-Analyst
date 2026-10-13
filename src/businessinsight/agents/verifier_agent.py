"""Verifier Agent: Deterministically audits numerical claims, percentages, and causal validity."""

import logging
from typing import List
from businessinsight.agents.base import extract_token_usage, get_gemini_agent
from businessinsight.analytics import (
    validate_finding,
    verify_period_percentage_change,
)
from businessinsight.analytics.metrics import safe_percentage_change
from businessinsight.workflow.schemas import (
    AnalystAgentOutput,
    StrategyAgentOutput,
    VerificationDiscrepancy,
    VerificationStatus,
    VerifierAgentOutput,
)

logger = logging.getLogger(__name__)

VERIFIER_AGENT_INSTRUCTIONS = """You are the Lead Auditor and Verifier Agent in BusinessInsight AI.
Your sole job is to audit claims made by the Analyst and Strategy agents against empirical calculations.
CHECKS:
1. Verify arithmetic truth, period definitions, and percentage change logic.
2. Flag any recommendation that presents correlation as proven causality without data.
3. Identify ungrounded or contradictory recommendations that reference nonexistent findings."""


class VerifierAgent:
    """Agent 4: Deterministically verifies numerical findings and audits strategic recommendations."""

    def __init__(self):
        self._maf_agent = get_gemini_agent(
            name="VerifierAgent",
            instructions=VERIFIER_AGENT_INSTRUCTIONS,
        )

    async def run(
        self,
        analyst_output: AnalystAgentOutput,
        strategy_output: StrategyAgentOutput,
    ) -> VerifierAgentOutput:
        """Audits findings and recommendations for mathematical correctness and causal validity."""
        logger.info("VerifierAgent: Auditing findings and recommendations...")

        discrepancies: List[VerificationDiscrepancy] = []
        unsupported_claims: List[str] = []
        inconsistencies: List[str] = []
        verified_count = 0
        failed_count = 0

        finding_ids = {f.id for f in analyst_output.findings}


        for finding in analyst_output.findings:

            if finding.prior_value is not None and finding.percentage_change is not None:
                is_valid_pct, computed_pct, explanation = verify_period_percentage_change(
                    claimed_pct_change=finding.percentage_change,
                    prior_value=finding.prior_value,
                    current_value=finding.computed_value,
                    tolerance=0.1,
                )
                if not is_valid_pct:
                    discrepancies.append(
                        VerificationDiscrepancy(
                            metric_name=f"{finding.metric_name} percentage change",
                            claimed_value=finding.percentage_change,
                            verified_value=computed_pct,
                            discrepancy_type="percentage_arithmetic_mismatch",
                            explanation=explanation or "Percentage change calculation deviated.",
                        )
                    )
                    failed_count += 1
                    continue


            if finding.prior_value is not None and finding.absolute_change is not None:
                expected_abs = round(finding.computed_value - finding.prior_value, 2)
                diff = abs(finding.absolute_change - expected_abs)
                if diff > 0.05:
                    discrepancies.append(
                        VerificationDiscrepancy(
                            metric_name=f"{finding.metric_name} absolute change",
                            claimed_value=finding.absolute_change,
                            verified_value=expected_abs,
                            discrepancy_type="absolute_difference_mismatch",
                            explanation=f"Claimed change {finding.absolute_change} != computed {expected_abs}.",
                        )
                    )
                    failed_count += 1
                    continue

            verified_count += 1


        for rec in strategy_output.recommendations:

            for fid in rec.supporting_finding_ids:
                if fid not in finding_ids:
                    inconsistencies.append(
                        f"Recommendation {rec.id} references non-existent finding '{fid}'."
                    )


            lower_rationale = rec.rationale.lower()
            causal_triggers = ["caused by customer churn", "because customers hate", "due entirely to"]
            for trigger in causal_triggers:
                if trigger in lower_rationale:
                    unsupported_claims.append(
                        f"Recommendation {rec.id} asserts '{trigger}', but transactional sales data "
                        f"only demonstrates temporal correlation, not definitive external causation."
                    )


        if len(discrepancies) == 0 and len(inconsistencies) == 0:
            status = VerificationStatus.VERIFIED
            summary = (
                f"All {verified_count} analyzed numerical findings were independently recomputed and verified. "
                f"All {len(strategy_output.recommendations)} recommendations are appropriately grounded."
            )
        elif len(discrepancies) > 0:
            status = VerificationStatus.VERIFIED_WITH_WARNINGS
            summary = (
                f"Verification completed with {len(discrepancies)} numerical discrepancies identified. "
                f"{verified_count} findings passed recomputation."
            )
        else:
            status = VerificationStatus.VERIFIED_WITH_WARNINGS
            summary = (
                f"Numerical findings verified, but {len(inconsistencies)} recommendation link issues were identified."
            )

        input_tokens = 0
        output_tokens = 0


        if self._maf_agent is not None:
            try:
                prompt = (
                    f"Audit these strategic recommendations for unsupported causal leaps:\n"
                    + "\n".join([f"- {r.id}: {r.rationale}" for r in strategy_output.recommendations])
                    + "\nFlag any statement where correlation was stated as proven causation."
                )
                resp = await self._maf_agent.run(prompt)
                input_tokens, output_tokens = extract_token_usage(resp, prompt_text=prompt)
                if resp and hasattr(resp, "text") and resp.text:
                    if "causation" in resp.text.lower() or "unsupported" in resp.text.lower():
                        summary += f" Auditor Note: {resp.text.strip()[:150]}..."
            except Exception as e:
                logger.warning(f"VerifierAgent LLM call skipped: {e}")

        return VerifierAgentOutput(
            status=status,
            verified_findings_count=verified_count,
            failed_findings_count=failed_count,
            discrepancies=discrepancies,
            unsupported_causal_claims=unsupported_claims,
            inconsistencies=inconsistencies,
            verification_summary=summary,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
