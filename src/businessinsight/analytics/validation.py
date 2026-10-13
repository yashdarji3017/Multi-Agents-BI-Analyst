"""Deterministic numerical and factual verification of analytical findings."""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel

from businessinsight.analytics.metrics import calculate_revenue, safe_percentage_change


class VerificationDiscrepancy(BaseModel):
    """Specific discrepancy detected during analytical verification."""

    metric_name: str
    claimed_value: Any
    verified_value: Any
    tolerance_pct: float = 0.01
    discrepancy_type: str
    explanation: str


class FindingVerificationResult(BaseModel):
    """Structured result of verifying an individual finding."""

    finding_id: str
    is_verified: bool
    confidence_score: float
    discrepancies: List[VerificationDiscrepancy] = []
    notes: str = ""


def validate_finding(
    finding_id: str,
    claimed_metric: str,
    claimed_value: float,
    computed_value: float,
    tolerance: float = 0.02,
) -> FindingVerificationResult:
    """Deterministically validates a single numerical finding against ground truth computed values."""
    discrepancies: List[VerificationDiscrepancy] = []


    if computed_value == 0:
        is_match = abs(claimed_value - computed_value) < 1e-4
    else:
        relative_diff = abs(claimed_value - computed_value) / abs(computed_value)
        is_match = relative_diff <= tolerance

    if not is_match:
        discrepancies.append(
            VerificationDiscrepancy(
                metric_name=claimed_metric,
                claimed_value=claimed_value,
                verified_value=computed_value,
                tolerance_pct=tolerance * 100,
                discrepancy_type="numerical_mismatch",
                explanation=(
                    f"Claimed value {claimed_value:,.2f} deviates from computed truth "
                    f"{computed_value:,.2f} by more than {tolerance*100:.1f}% tolerance."
                ),
            )
        )

    return FindingVerificationResult(
        finding_id=finding_id,
        is_verified=len(discrepancies) == 0,
        confidence_score=1.0 if len(discrepancies) == 0 else 0.0,
        discrepancies=discrepancies,
        notes="Deterministically recomputed and verified."
        if len(discrepancies) == 0
        else "Discrepancy detected during recomputation.",
    )


def verify_period_percentage_change(
    claimed_pct_change: float,
    prior_value: float,
    current_value: float,
    tolerance: float = 0.05,
) -> tuple[bool, Optional[float], Optional[str]]:
    """Verifies that a claimed percentage change matches ((current - prior) / prior) * 100."""
    computed_pct = safe_percentage_change(current_value, prior_value)
    if computed_pct is None:
        if claimed_pct_change == 0.0:
            return True, None, "Prior period value is 0; percentage change treated as 0."
        return False, None, "Prior period value is 0; percentage change is undefined (division by zero)."

    diff = abs(claimed_pct_change - computed_pct)
    if diff <= tolerance:
        return True, computed_pct, None
    return (
        False,
        computed_pct,
        f"Claimed {claimed_pct_change:.2f}% deviates from computed {computed_pct:.2f}% (diff: {diff:.2f}%).",
    )
