"""In-memory execution tracing for Multi-Agent Workflow runs with Gemini native token metrics."""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepTrace(BaseModel):
    """Execution trace for an individual agent step with token counts."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_name: str
    status: str = "pending"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    input_summary: str = ""
    output_summary: str = ""
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def complete(
        self,
        output_summary: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark the step as completed and record token metrics."""
        self.end_time = time.time()
        self.duration_seconds = round(self.end_time - self.start_time, 3)
        self.status = "completed"
        if output_summary:
            self.output_summary = output_summary
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        if metadata:
            self.metadata.update(metadata)

    def fail(self, error_message: str) -> None:
        """Mark the step as failed."""
        self.end_time = time.time()
        self.duration_seconds = round(self.end_time - self.start_time, 3)
        self.status = "failed"
        self.error_message = error_message


class AgentExecutionTrace(BaseModel):
    """Complete workflow execution trace held in memory."""

    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    steps: List[StepTrace] = Field(default_factory=list)
    status: str = "in_progress"


    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    token_usage_by_agent: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    def start_step(self, agent_name: str, input_summary: str = "") -> StepTrace:
        """Start and record a new step."""
        step = StepTrace(agent_name=agent_name, input_summary=input_summary, status="running")
        self.steps.append(step)
        return step

    def finalize(self, status: str = "completed") -> None:
        """Finalize the trace and compute per-agent token aggregations."""
        self.completed_at = time.time()
        self.total_duration_seconds = round(self.completed_at - self.created_at, 3)
        self.status = status

        self.total_input_tokens = sum(s.input_tokens for s in self.steps)
        self.total_output_tokens = sum(s.output_tokens for s in self.steps)
        self.total_tokens = sum(s.total_tokens for s in self.steps)

        self.token_usage_by_agent = {
            s.agent_name: {
                "input_tokens": s.input_tokens,
                "output_tokens": s.output_tokens,
                "total_tokens": s.total_tokens,
            }
            for s in self.steps
        }
