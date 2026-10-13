"""Workflow package for state management and agent orchestration."""

from .schemas import (
    AnalysisSettings,
    AnalystAgentOutput,
    AnalystFinding,
    ComparisonMode,
    DataAgentOutput,
    FindingType,
    Recommendation,
    ReportAgentOutput,
    StrategyAgentOutput,
    VerificationStatus,
    VerifierAgentOutput,
)
from .state import AnalysisWorkflowState


def get_orchestrator():
    """Lazy loader for MultiAgentOrchestrator to prevent circular imports."""
    from .orchestrator import MultiAgentOrchestrator
    return MultiAgentOrchestrator


__all__ = [
    "AnalysisWorkflowState",
    "AnalysisSettings",
    "ComparisonMode",
    "DataAgentOutput",
    "AnalystAgentOutput",
    "AnalystFinding",
    "FindingType",
    "Recommendation",
    "StrategyAgentOutput",
    "VerifierAgentOutput",
    "VerificationStatus",
    "ReportAgentOutput",
    "get_orchestrator",
]
