from __future__ import annotations

from abc import abstractmethod
from pathlib import Path

from pydantic_ai.models.test import TestModel
from pydantic_ai_backends.backends import LocalBackend
from pydantic_deep import create_deep_agent, create_default_deps

from diviora_kernel.lanes.base import LaneWorker
from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest


class DeepAgentLaneWorker(LaneWorker):
    """Bounded adapter for pydantic-deep workers under kernel authority."""

    deep_agent_runtime: str = "pydantic-deep"

    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        artifact_content, lane_memory, audit = self._run_lane(task=task, step=step, run_dir=run_dir)
        artifact_name = self._write_lane_artifact(run_dir=run_dir, step=step, content=artifact_content)
        lane_memory_artifact = self._write_lane_memory_artifact(run_dir=run_dir, step=step, content=lane_memory)

        return StepResult(
            step_id=step.step_id,
            success=True,
            status="completed",
            output_summary=(artifact_content.splitlines()[0][:200] if artifact_content else "Lane completed"),
            artifacts=[artifact_name, lane_memory_artifact],
            metadata=self._metadata(
                task=task,
                step=step,
                artifact_name=artifact_name,
                lane_memory_artifact=lane_memory_artifact,
                audit=audit,
            ),
        )

    def _metadata(
        self,
        task: TaskRequest,
        step: PlanStep,
        artifact_name: str,
        lane_memory_artifact: str,
        audit: dict[str, object],
    ) -> dict[str, object]:
        return {
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "worker_runtime": self.worker_runtime,
            "execution_mode": self.execution_mode,
            "requires_approval": self._requires_approval(step),
            "step_inputs": {
                "task_id": task.task_id,
                "task_title": task.title,
                "task_type": getattr(task.task_type, "value", task.task_type),
                "step_name": step.name,
                "step_description": step.description,
                "task_context_summary": self._task_context_summary(task),
            },
            "lane_metadata": {
                "side_effect_capable": self.side_effect_capable,
                "inspection_only": not self.side_effect_capable,
                "runtime_adapter": "deep-agent-lane-adapter",
                "artifact": artifact_name,
                "lane_memory_artifact": lane_memory_artifact,
                "lane_memory_canonical": False,
                **audit,
            },
            "canonical_truth_source": "kernel_ledger",
            "lane_memory_canonical": False,
        }

    def _write_lane_artifact(self, run_dir: Path, step: PlanStep, content: str) -> str:
        artifact_name = f"{step.step_id}_{self.default_artifact_name}"
        (run_dir / artifact_name).write_text(content, encoding="utf-8")
        return artifact_name

    def _write_lane_memory_artifact(self, run_dir: Path, step: PlanStep, content: str) -> str:
        artifact_name = f"{step.step_id}_lane_memory.md"
        (run_dir / artifact_name).write_text(content, encoding="utf-8")
        return artifact_name

    @property
    def worker_runtime(self) -> str:
        return self.deep_agent_runtime

    def _requires_approval(self, step: PlanStep) -> bool:
        return bool(step.side_effectful)

    @abstractmethod
    def _run_lane(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> tuple[str, str, dict[str, object]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def default_artifact_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def lane_goal(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def output_title(self) -> str:
        raise NotImplementedError

    def _run_deep_agent(
        self,
        *,
        task: TaskRequest,
        step: PlanStep,
        run_dir: Path,
        output_artifact_name: str,
    ) -> tuple[str, str, dict[str, object]]:
        backend = LocalBackend(
            root_dir=run_dir,
            allowed_directories=[str(run_dir)],
            enable_execute=False,
        )
        deps = create_default_deps(backend=backend)
        agent = create_deep_agent(
            model=TestModel(call_tools=[]),
            instructions=self._agent_instructions(run_dir=run_dir, output_artifact_name=output_artifact_name),
            backend=backend,
            include_execute=False,
            include_web=False,
            include_memory=False,
            include_skills=False,
            include_subagents=False,
            include_general_purpose_subagent=False,
            include_plan=False,
            include_filesystem=False,
            include_todo=False,
            include_teams=False,
            include_history_archive=False,
            cost_tracking=False,
            context_discovery=False,
        )

        prompt = self._agent_prompt(task=task, step=step, run_dir=run_dir, output_artifact_name=output_artifact_name)
        response = agent.run_sync(prompt, deps=deps)
        response_text = str(response.output).strip() or "No lane output"

        artifact_content = (
            f"# {self.output_title}: {task.title}\n\n"
            f"## Goal\n{self.lane_goal}\n\n"
            f"## Step\n- id: {step.step_id}\n- name: {step.name}\n- description: {step.description}\n\n"
            f"## Deep Agent Response\n{response_text}\n"
        )

        lane_memory = (
            "# Lane Memory (NON_CANONICAL)\n\n"
            "This artifact is audit-only and never canonical truth.\n\n"
            f"- Worker: {self.worker_id}\n"
            f"- Execution mode: {self.execution_mode}\n"
            f"- Runtime: {self.worker_runtime}\n"
            f"- Prompt hash input summary: {self._task_context_summary(task)}\n"
            f"- Response excerpt: {response_text[:240]}\n"
        )

        audit = {
            "bounded_backend": "LocalBackend",
            "backend_root": str(run_dir),
            "allowed_directories": [str(run_dir)],
            "shell_execution_enabled": False,
            "filesystem_tools_enabled": False,
            "memory_enabled": False,
        }
        return artifact_content, lane_memory, audit

    def _task_context_summary(self, task: TaskRequest) -> str:
        keys = sorted(task.input_data.keys())
        return f"{task.title} | {task.description[:120]} | input_keys={keys}"

    def _agent_instructions(self, *, run_dir: Path, output_artifact_name: str) -> str:
        return (
            f"You are the {self.worker_id} lane runtime. "
            f"Produce content for {output_artifact_name}. "
            f"You may only operate within run_dir={run_dir}. "
            "Do not execute shell commands. "
            "Do not write outside run_dir. "
            "Return concise markdown only."
        )

    def _agent_prompt(self, *, task: TaskRequest, step: PlanStep, run_dir: Path, output_artifact_name: str) -> str:
        return (
            f"Task ID: {task.task_id}\n"
            f"Task Title: {task.title}\n"
            f"Task Description: {task.description}\n"
            f"Task Input Data: {task.input_data}\n"
            f"Step ID: {step.step_id}\n"
            f"Step Name: {step.name}\n"
            f"Step Description: {step.description}\n"
            f"Required artifact filename: {output_artifact_name}\n"
            f"Run dir boundary: {run_dir}\n"
            "Safety: no shell execution; no writes outside run_dir."
        )
