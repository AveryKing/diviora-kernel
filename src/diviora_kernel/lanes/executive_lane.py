from __future__ import annotations

from diviora_kernel.lanes.deep_agent_base import DeepAgentLaneWorker
from diviora_kernel.schemas import PlanStep, TaskRequest


class ExecutiveDeepAgentWorker(DeepAgentLaneWorker):
    """Chief-of-staff style lane for bounded planning and status framing."""

    @property
    def worker_id(self) -> str:
        return "lane.executive.deep_agent.v1"

    @property
    def worker_type(self) -> str:
        return "executive_deep_agent"

    @property
    def execution_mode(self) -> str:
        return "inspection_planning"

    @property
    def side_effect_capable(self) -> bool:
        return False

    @property
    def default_artifact_name(self) -> str:
        return "proposed_plan.md"

    def _run_lane(self, task: TaskRequest, step: PlanStep) -> str:
        return (
            f"# Proposed Plan for {task.title}\n\n"
            "## Objective\n"
            f"{task.description}\n\n"
            "## Decisions\n"
            "1. Keep kernel contracts as canonical authority.\n"
            "2. Sequence execution into bounded and auditable steps.\n"
            "3. Escalate side effects through approval semantics only.\n\n"
            "## Current Status\n"
            f"Prepared executive lane output for step '{step.step_id}'.\n"
        )
