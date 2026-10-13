"""Data Agent: Validates raw data, establishes canonical schema, and checks data quality."""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd

from businessinsight.agents.base import extract_token_usage, get_gemini_agent
from businessinsight.config import settings
from businessinsight.data.loader import DataLoader
from businessinsight.workflow.schemas import DataAgentOutput

logger = logging.getLogger(__name__)

DATA_AGENT_INSTRUCTIONS = """You are the Data Agent in BusinessInsight AI.
Your role is to inspect the uploaded dataset profile, summarize data hygiene risks,
identify analytical limitations (such as missing categories, unparsed dates, or negative values),
and produce a concise, professional assessment of dataset readiness for financial analytics.
Never allow unsafe files, never bypass schema validation, and adhere strictly to deterministic checks."""


class DataAgent:
    """Agent 1: Inspects, validates, profiles, and gates the incoming CSV dataset."""

    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or settings.dataset_path
        self.loader = DataLoader(self.dataset_path)
        self._maf_agent = get_gemini_agent(
            name="DataAgent",
            instructions=DATA_AGENT_INSTRUCTIONS,
        )

    async def run(self) -> DataAgentOutput:
        """Executes data profiling, validation, and schema mapping deterministically."""
        logger.info(f"DataAgent: Inspecting and loading dataset from {self.dataset_path}...")


        canonical_df, profile = self.loader.load_canonical()

        warnings = list(profile.quality_summary.warnings)
        limitations = []
        input_tokens = 0
        output_tokens = 0


        if "profit" not in profile.column_mapping:
            limitations.append("Dataset lacks Profit column; profitability metrics cannot be evaluated.")
        if "discount" not in profile.column_mapping:
            limitations.append("Dataset lacks Discount column; price elasticity and discounting cannot be tracked.")
        if "segment" not in profile.column_mapping:
            limitations.append("Customer Segment column not present; segmentation breakdowns are unavailable.")


        if profile.quality_summary.duplicate_rows > 0:
            limitations.append(
                f"Contains {profile.quality_summary.duplicate_rows} duplicate rows which could affect volume totals."
            )


        if self._maf_agent is not None:
            try:

                raw_csv_content = canonical_df.to_csv(index=False)


                prompt = (
                    f"Inspect all {len(canonical_df)} records of this CSV dataset for data hygiene issues:\n\n"
                    f"{raw_csv_content}\n\n"
                    f"List any data anomalies, formatting issues, or errors."
                )

                response = await self._maf_agent.run(prompt)

                input_tokens, output_tokens = extract_token_usage(response, prompt_text=prompt)
                if response and hasattr(response, "text") and response.text:
                    warnings.append(f"AI Observation: {response.text.strip()}")
            except Exception as e:
                logger.warning(f"DataAgent LLM enhancement skipped: {e}")

        return DataAgentOutput(
            is_valid_for_analysis=profile.quality_summary.is_valid_for_analysis,
            dataset_profile=profile,
            warnings=warnings,
            limitations=limitations,
            total_records=profile.quality_summary.total_rows,
            date_range_start=profile.quality_summary.date_range_start,
            date_range_end=profile.quality_summary.date_range_end,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def get_loaded_dataframe(self) -> pd.DataFrame:
        """Returns the loaded canonical DataFrame."""
        df, _ = self.loader.load_canonical()
        return df
