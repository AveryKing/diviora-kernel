from __future__ import annotations

from diviora_kernel.lanes.deep_agent_base import DeepAgentLaneWorker
from diviora_kernel.schemas import PlanStep, TaskRequest


class ExecutiveDeepAgentWorker(DeepAgentLaneWorker):
    """Chief-of-staff lane for bounded inspection/planning output."""

    @property
    def worker_id(self) -> str:
        return "lane.executive.deep_agent.v1"

    @property
    def worker_type(self) -> str:
        return "executive_deep_agent"

    @property
    def execution_mode(self) -> str:
        return "inspection"

    @property
    def side_effect_capable(self) -> bool:
        return False

    @property
    def default_artifact_name(self) -> str:
        return "proposed_plan.md"

    @property
    def lane_goal(self) -> str:
        return "Inspection/planning only. No shell execution and no external side effects."

    @property
    def output_title(self) -> str:
        return "Proposed Plan"

    def _requires_approval(self, step: PlanStep) -> bool:
        return False

    def _run_lane(self, task: TaskRequest, step: PlanStep, run_dir):
        artifact_name = f"{step.step_id}_{self.default_artifact_name}"
        return self._run_deep_agent(task=task, step=step, run_dir=run_dir, output_artifact_name=artifact_name)
