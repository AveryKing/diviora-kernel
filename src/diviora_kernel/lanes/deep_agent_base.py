from __future__ import annotations

from abc import abstractmethod
from pathlib import Path

from diviora_kernel.lanes.base import LaneWorker
from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest


class DeepAgentLaneWorker(LaneWorker):
    """Bounded adapter for deep-agent style runtimes under kernel authority."""

    deep_agent_runtime: str = "pydantic-deepagents(stub)"

    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        lane_output = self._run_lane(task=task, step=step)
        artifact_name = self._write_lane_artifact(run_dir=run_dir, step=step, content=lane_output)
        return StepResult(
            step_id=step.step_id,
            success=True,
            status="completed",
            output_summary=lane_output.splitlines()[0][:200] if lane_output else "Lane completed",
            artifacts=[artifact_name],
            metadata=self._metadata(task=task, step=step, artifact_name=artifact_name),
        )

    def _metadata(self, task: TaskRequest, step: PlanStep, artifact_name: str) -> dict[str, object]:
        return {
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "worker_runtime": self.worker_runtime,
            "execution_mode": self.execution_mode,
            "requires_approval": bool(step.side_effectful),
            "step_inputs": {
                "task_id": task.task_id,
                "task_title": task.title,
                "task_type": getattr(task.task_type, "value", task.task_type),
                "step_name": step.name,
                "step_description": step.description,
            },
            "lane_metadata": {
                "side_effect_capable": self.side_effect_capable,
                "inspection_only": not self.side_effect_capable,
                "runtime_adapter": "deep-agent-lane-adapter",
                "artifact": artifact_name,
            },
            "canonical_truth_source": "kernel_ledger",
            "lane_memory_canonical": False,
        }

    def _write_lane_artifact(self, run_dir: Path, step: PlanStep, content: str) -> str:
        artifact_name = f"{step.step_id}_{self.default_artifact_name}"
        (run_dir / artifact_name).write_text(content, encoding="utf-8")
        return artifact_name

    @property
    def worker_runtime(self) -> str:
        return self.deep_agent_runtime

    @property
    @abstractmethod
    def default_artifact_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _run_lane(self, task: TaskRequest, step: PlanStep) -> str:
        raise NotImplementedError
