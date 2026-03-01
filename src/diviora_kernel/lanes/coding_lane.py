from __future__ import annotations

from pathlib import Path

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

    @property
    def lane_goal(self) -> str:
        return "Coding planning mode by default. No shell execution. Approved side effects are future-gated and run-dir bounded."

    @property
    def output_title(self) -> str:
        return "Code Plan"

    def _run_lane(self, task: TaskRequest, step: PlanStep, run_dir: Path):
        artifact_name = f"{step.step_id}_{self.default_artifact_name}"
        return self._run_deep_agent(task=task, step=step, run_dir=run_dir, output_artifact_name=artifact_name)
