from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest
from diviora_kernel.workers.base import Worker


class LLMResponse(BaseModel):
    summary: str
    details: str


class LLMWorker(Worker):
    """Typed LLM worker using PydanticAI with deterministic test model for v0."""

    def __init__(self) -> None:
        self._agent = Agent(
            TestModel(),
            result_type=LLMResponse,
            system_prompt=(
                "You are a disciplined kernel worker. "
                "Never fabricate success. Keep outputs concise and explicit."
            ),
        )

    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        prompt = step.prompt or f"Task: {task.title}. Description: {task.description}."
        response = self._agent.run_sync(prompt).output

        artifact_path = run_dir / f"{step.step_id}_llm_output.md"
        artifact_path.write_text(
            f"# {step.name}\n\n## Summary\n{response.summary}\n\n## Details\n{response.details}\n",
            encoding="utf-8",
        )

        return StepResult(
            step_id=step.step_id,
            success=True,
            status="completed",
            output_summary=response.summary,
            artifacts=[artifact_path.name],
            metadata={"worker": "llm"},
        )
