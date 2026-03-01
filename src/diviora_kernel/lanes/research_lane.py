from __future__ import annotations

from pathlib import Path

from diviora_kernel.lanes.deep_agent_base import DeepAgentLaneWorker
from diviora_kernel.schemas import PlanStep, TaskRequest


class ResearchDeepAgentWorker(DeepAgentLaneWorker):
    """Research lane for bounded synthesis with artifact-first outputs."""

    @property
    def worker_id(self) -> str:
        return "lane.research.deep_agent.v1"

    @property
    def worker_type(self) -> str:
        return "research_deep_agent"

    @property
    def execution_mode(self) -> str:
        return "research"

    @property
    def side_effect_capable(self) -> bool:
        return False

    @property
    def default_artifact_name(self) -> str:
        return "research_notes.md"

    @property
    def lane_goal(self) -> str:
        return "Bounded research mode with shell execution disabled unless kernel approval policy allows future extension."

    @property
    def output_title(self) -> str:
        return "Research Notes"

    def _requires_approval(self, step: PlanStep) -> bool:
        return False

    def _run_lane(self, task: TaskRequest, step: PlanStep, run_dir: Path):
        artifact_name = f"{step.step_id}_{self.default_artifact_name}"
        return self._run_deep_agent(task=task, step=step, run_dir=run_dir, output_artifact_name=artifact_name)
