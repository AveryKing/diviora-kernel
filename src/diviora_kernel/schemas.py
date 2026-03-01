from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    RESEARCH_REPORT = "research_report"
    CODE_TASK = "code_task"
    DECISION_MEMO = "decision_memo"


class ApprovalMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class WorkerType(str, Enum):
    LLM = "llm"
    SHELL = "shell"
    EXECUTIVE_DEEP_AGENT = "executive_deep_agent"
    RESEARCH_DEEP_AGENT = "research_deep_agent"
    CODING_DEEP_AGENT = "coding_deep_agent"


class FinalState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    PARTIAL = "PARTIAL"


class TaskRequest(BaseModel):
    task_id: str
    title: str
    description: str
    task_type: TaskType
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    requested_by: str = "unknown"
    input_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanStep(BaseModel):
    step_id: str
    name: str
    description: str
    worker_type: WorkerType
    side_effectful: bool = False
    command: list[str] | None = None
    prompt: str | None = None


class Plan(BaseModel):
    task_id: str
    rationale: str
    steps: list[PlanStep]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer: str
    reason: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StepResult(BaseModel):
    step_id: str
    success: bool
    status: str
    output_summary: str
    artifacts: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class VerificationResult(BaseModel):
    passed: bool
    checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RunOutcome(BaseModel):
    final_state: FinalState
    summary: str
    completed_steps: int
    failed_steps: int


class RunRecord(BaseModel):
    run_id: str
    task_request: TaskRequest
    plan: Plan
    approval_decision: ApprovalDecision | None = None
    step_results: list[StepResult] = Field(default_factory=list)
    verification: VerificationResult | None = None
    outcome: RunOutcome
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PackTaskEntry(BaseModel):
    file: str
    title: str
    task_type: TaskType


class PackManifest(BaseModel):
    name: str
    created_at: datetime
    goal: str
    tasks: list[PackTaskEntry]
