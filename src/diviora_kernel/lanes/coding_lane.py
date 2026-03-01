from __future__ import annotations

from diviora_kernel.lanes.deep_agent_base import DeepAgentLaneWorker
from diviora_kernel.schemas import PlanStep, TaskRequest


class CodingDeepAgentWorker(DeepAgentLaneWorker):
    """Coding lane for bounded implementation planning under kernel approval control."""

    @property
    def worker_id(self) -> str:
        return "lane.coding.deep_agent.v1"

    @property
    def worker_type(self) -> str:
        return "coding_deep_agent"

    @property
    def execution_mode(self) -> str:
        return "coding_planning"

    @property
    def side_effect_capable(self) -> bool:
        return True

    @property
    def default_artifact_name(self) -> str:
        return "code_plan.md"

    def _run_lane(self, task: TaskRequest, step: PlanStep) -> str:
        return (
            f"# Code Plan: {task.title}\n\n"
            "## Scope\n"
            f"{task.description}\n\n"
            "## Proposed Changes\n"
            "1. Update typed interfaces first.\n"
            "2. Implement minimal adapter logic second.\n"
            "3. Verify behavior with focused tests.\n\n"
            "## Implementation Notes\n"
            f"Prepared bounded coding output for step '{step.step_id}'.\n"
        )
