"""Strategy Agent: Formulates evidence-linked hypotheses and business recommendations."""

import logging
from typing import List
from businessinsight.agents.base import extract_token_usage, get_gemini_agent
from businessinsight.workflow.schemas import (
    AnalystAgentOutput,
    EffortLevel,
    ImpactLevel,
    Recommendation,
    StrategyAgentOutput,
)

logger = logging.getLogger(__name__)

STRATEGY_AGENT_INSTRUCTIONS = """You are the Chief Strategy Agent in BusinessInsight AI.
Your role is to formulate prioritized, evidence-backed commercial recommendations grounded strictly in the Analyst Agent's empirical findings.
GOVERNANCE RULES:
1. Always distinguish between observed empirical facts, hypotheses, and assumptions.
2. Never claim direct causation (e.g. 'sales dropped because of customer dissatisfaction') unless explicit causal data exists. Treat changes as correlation or temporal co-occurrence.
3. Every recommendation MUST reference at least one supporting finding ID (e.g., F-01, F-02).
4. Clearly state what additional data is required to validate hypotheses."""


class StrategyAgent:
    """Agent 3: Formulates strategic recommendations tied to analytical findings."""

    def __init__(self):
        self._maf_agent = get_gemini_agent(
            name="StrategyAgent",
            instructions=STRATEGY_AGENT_INSTRUCTIONS,
        )

    async def run(
        self,
        analyst_output: AnalystAgentOutput,
        business_question: str,
        max_recommendations: int = 5,
    ) -> StrategyAgentOutput:
        """Generates evidence-backed recommendations linked to empirical findings."""
        logger.info("StrategyAgent: Synthesizing strategic recommendations...")

        recommendations: List[Recommendation] = []
        hypotheses: List[str] = []
        unresolved: List[str] = []

        findings_map = {f.id: f for f in analyst_output.findings}


        decline_finding = next((f for f in analyst_output.findings if f.finding_type.value == "product_decline"), None)
        if decline_finding and analyst_output.declining_products:
            top_dec = analyst_output.declining_products[0]
            recommendations.append(
                Recommendation(
                    id="REC-01",
                    title=f"Conduct Catalog & Pricing Audit on {top_dec.product_name[:35]}...",
                    action=(
                        f"Review current pricing tier, supplier lead times, and promotional positioning for "
                        f"'{top_dec.product_name[:40]}' within category '{top_dec.category}'."
                    ),
                    rationale=(
                        f"Product experienced a ${abs(top_dec.absolute_sales_change):,.2f} revenue decline "
                        f"({top_dec.percentage_sales_change or 0.0:+.1f}%), driving "
                        f"{top_dec.contribution_to_total_decline_pct or 0.0:.1f}% of total observed product contractions."
                    ),
                    supporting_finding_ids=[decline_finding.id],
                    potential_impact=ImpactLevel.HIGH,
                    implementation_effort=EffortLevel.QUICK_WIN,
                    confidence_description="High empirical confidence in revenue drop; moderate confidence in commercial etiology.",
                    assumptions=[
                        "Assuming product was not intentionally phased out or sunsetted.",
                        "Assuming inventory stocking was sufficient to meet baseline demand.",
                    ],
                    suggested_follow_up=[
                        "Examine stockout/inventory replenishment logs during the contraction quarter.",
                        "Inspect competitor pricing for identical models.",
                    ],
                )
            )
            hypotheses.append(
                f"Hypothesis 1: Demand for '{top_dec.product_name[:30]}' softened due to price uncompetitiveness or supply chain stockouts."
            )
            unresolved.append("Did inventory stockouts constrain fulfilled orders during this period?")


        reg_finding = next((f for f in analyst_output.findings if f.finding_type.value == "regional_performance"), None)
        if reg_finding:
            recommendations.append(
                Recommendation(
                    id="REC-02",
                    title="Territory Account Review in Underperforming Region",
                    action=(
                        f"Audit sales distribution and customer account retention in {reg_finding.dimension_context} "
                        "with regional commercial leads."
                    ),
                    rationale=(
                        f"Regional revenue exhibited a negative contraction of "
                        f"${abs(reg_finding.absolute_change or 0.0):,.2f} ({reg_finding.percentage_change or 0.0:+.1f}%)."
                    ),
                    supporting_finding_ids=[reg_finding.id],
                    potential_impact=ImpactLevel.HIGH,
                    implementation_effort=EffortLevel.MEDIUM_TERM,
                    confidence_description="High empirical verification from territorial transaction logs.",
                    assumptions=[
                        "Sales territories have remained stable without boundary redistricting.",
                        "Macroeconomic conditions in territory are aligned with general market trends.",
                    ],
                    suggested_follow_up=[
                        "Analyze corporate vs. consumer segment split within the territory.",
                        "Assess sales rep turnover and enterprise pipeline health in the region.",
                    ],
                )
            )
            hypotheses.append(
                f"Hypothesis 2: Performance decline in {reg_finding.dimension_context} reflects key account attrition rather than systemic market rejection."
            )
            unresolved.append(f"Were top B2B client contracts lost or deferred in {reg_finding.dimension_context}?")


        margin_finding = next((f for f in analyst_output.findings if f.finding_type.value == "margin_anomaly"), None)
        if margin_finding or any(a.anomaly_type == "severe_negative_profit" for a in analyst_output.anomalies):
            fid = [margin_finding.id] if margin_finding else []
            recommendations.append(
                Recommendation(
                    id="REC-03",
                    title="Implement Guardrails on Discretionary Discounting",
                    action=(
                        "Cap discretionary discounts at 20% for low-margin SKUs and require managerial sign-off "
                        "for discounts exceeding 30%."
                    ),
                    rationale=(
                        "Multiple transactions with deep discounts (>50%) generated severe negative net profits, "
                        "eroding overall category margins."
                    ),
                    supporting_finding_ids=fid,
                    potential_impact=ImpactLevel.MEDIUM,
                    implementation_effort=EffortLevel.QUICK_WIN,
                    confidence_description="Very high empirical evidence from negative net margin transactions.",
                    assumptions=[
                        "Discounts above 40% are not mandated by contractual loss-leader strategies.",
                    ],
                    suggested_follow_up=[
                        "Audit sales rep compensation incentives regarding gross revenue vs. gross margin.",
                    ],
                )
            )
            hypotheses.append(
                "Hypothesis 3: High discount allowances incentivized volume generation at the expense of transaction-level margin."
            )
            unresolved.append("Which customer segments or sales channels received the deepest discounts?")


        vol_finding = next((f for f in analyst_output.findings if f.finding_type.value == "volume_and_aov"), None)
        if vol_finding:
            recommendations.append(
                Recommendation(
                    id="REC-04",
                    title="Product Bundling & Upsell Initiative to Bolster Order Size",
                    action=(
                        "Deploy automated cross-sell recommendations for complementary office supplies and accessories "
                        "at checkout."
                    ),
                    rationale=(
                        f"Current average order value stands at ${analyst_output.summary_kpis.average_order_value:,.2f}. "
                        "Incremental basket expansion offers high operating leverage."
                    ),
                    supporting_finding_ids=[vol_finding.id],
                    potential_impact=ImpactLevel.MEDIUM,
                    implementation_effort=EffortLevel.MEDIUM_TERM,
                    confidence_description="Moderate confidence based on baseline transaction baskets.",
                    assumptions=[
                        "Customers purchase across related categories when offered relevant bundles.",
                    ],
                    suggested_follow_up=[
                        "Perform market-basket affinity analysis between Technology and Office Supplies categories.",
                    ],
                )
            )


        recs = recommendations[:max_recommendations]

        narrative = (
            f"Analysis regarding '{business_question}' indicates that revenue performance is driven by a combination of "
            f"selective product contractions and territorial variations. Strategic focus must prioritize pricing guardrails, "
            f"addressing regional decline in {reg_finding.dimension_context if reg_finding else 'key territories'}, "
            f"and mitigating deep discounting that erodes bottom-line profits."
        )

        input_tokens = 0
        output_tokens = 0


        if self._maf_agent is not None:
            try:
                prompt = (
                    f"Given these {len(recs)} evidence-linked recommendations:\n"
                    + "\n".join([f"- {r.id}: {r.title} (Action: {r.action})" for r in recs])
                    + f"\nBusiness Question: {business_question}\n"
                    + "Provide a 3-sentence executive strategic summary connecting these actions directly to financial recovery."
                )
                resp = await self._maf_agent.run(prompt)
                input_tokens, output_tokens = extract_token_usage(resp, prompt_text=prompt)
                if resp and hasattr(resp, "text") and resp.text:
                    narrative = resp.text.strip()
            except Exception as e:
                logger.warning(f"StrategyAgent LLM call skipped: {e}")

        return StrategyAgentOutput(
            recommendations=recs,
            strategic_narrative=narrative,
            identified_hypotheses=hypotheses,
            unresolved_questions=unresolved,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
