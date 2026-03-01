from __future__ import annotations

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
        return "research_analysis"

    @property
    def side_effect_capable(self) -> bool:
        return False

    @property
    def default_artifact_name(self) -> str:
        return "research_notes.md"

    def _run_lane(self, task: TaskRequest, step: PlanStep) -> str:
        return (
            f"# Research Notes: {task.title}\n\n"
            "## Bounded Inputs\n"
            f"- Description: {task.description}\n"
            f"- Input data: {task.input_data}\n\n"
            "## Options Matrix\n"
            "| Option | Benefit | Risk |\n"
            "|---|---|---|\n"
            "| A | Fast delivery | Lower confidence |\n"
            "| B | Balanced confidence | Moderate effort |\n"
            "| C | Deep validation | Slower delivery |\n\n"
            "## Recommendation\n"
            f"Use option B for step '{step.step_id}' with explicit verification handoff.\n"
        )
