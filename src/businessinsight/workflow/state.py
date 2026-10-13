"""In-memory multi-agent workflow state definition."""

import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field

from businessinsight.observability.tracing import AgentExecutionTrace
from businessinsight.workflow.schemas import (
    AnalysisSettings,
    AnalystAgentOutput,
    DataAgentOutput,
    ReportAgentOutput,
    StrategyAgentOutput,
    VerifierAgentOutput,
)


class AnalysisWorkflowState(BaseModel):
    """Encapsulates the in-memory state of an end-to-end multi-agent analysis session."""

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_question: str
    settings: AnalysisSettings = Field(default_factory=AnalysisSettings)


    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: str = "initialized"
    verification_round: int = 0
    error_message: Optional[str] = None


    trace: AgentExecutionTrace = Field(
        default_factory=lambda: AgentExecutionTrace(analysis_id="")
    )


    data_output: Optional[DataAgentOutput] = None
    analyst_output: Optional[AnalystAgentOutput] = None
    strategy_output: Optional[StrategyAgentOutput] = None
    verifier_output: Optional[VerifierAgentOutput] = None
    report_output: Optional[ReportAgentOutput] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.trace.analysis_id:
            self.trace.analysis_id = self.analysis_id
