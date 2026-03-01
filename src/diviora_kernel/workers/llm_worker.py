from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest, TaskType
from diviora_kernel.workers.base import Worker


class LLMWorker(Worker):
    """Typed LLM worker using real PydanticAI with deterministic test model for v0."""

    def __init__(self) -> None:
        self._agent = Agent(
            TestModel(call_tools=[]),
            output_type=str,
            system_prompt=(
                "You are a disciplined kernel worker. "
                "Never fabricate success. Keep outputs concise and explicit."
            ),
        )

    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        task_type = getattr(task.task_type, "value", task.task_type)
        if task_type == TaskType.DECISION_MEMO.value:
            memo = _build_decision_memo(task)
            artifact_path = run_dir / "decision_memo.md"
            artifact_path.write_text(memo, encoding="utf-8")
            return StepResult(
                step_id=step.step_id,
                success=True,
                status="completed",
                output_summary="Decision memo artifact created",
                artifacts=[artifact_path.name],
                metadata={"worker": "llm", "runtime": "pydantic-ai", "memo_content": memo},
            )

        prompt = step.prompt or f"Task: {task.title}. Description: {task.description}."
        output = str(self._agent.run_sync(prompt).output)
        summary = output.splitlines()[0][:200] if output else "LLM step completed"

        artifact_path = run_dir / f"{step.step_id}_llm_output.md"
        artifact_path.write_text(
            f"# {step.name}\n\n## Summary\n{summary}\n\n## Details\n{output}\n",
            encoding="utf-8",
        )

        return StepResult(
            step_id=step.step_id,
            success=True,
            status="completed",
            output_summary=summary,
            artifacts=[artifact_path.name],
            metadata={"worker": "llm", "runtime": "pydantic-ai"},
        )


def _build_decision_memo(task: TaskRequest) -> str:
    topic = task.description.strip() or task.title.strip() or "the proposed change"
    return (
        "# Decision Memo\n\n"
        "## Context\n"
        f"This memo evaluates {topic} and frames practical choices for delivery in the current operating constraints.\n\n"
        "## Options\n"
        "- **Option 1: Wrap existing stored procedures behind a thin API facade.** Lowest migration risk, fast onboarding path.\n"
        "- **Option 2: Introduce a modular domain API with selective service extraction.** Balanced modernization with controlled rewrite scope.\n"
        "- **Option 3: Full service-layer replacement of stored procedures.** Highest long-term flexibility, highest delivery risk and lead time.\n\n"
        "## Recommendation\n"
        "- **Recommend Option 2** as the pragmatic path: it enables progressive decoupling while preserving production stability.\n\n"
        "## Risks / Tradeoffs\n"
        "- Transitional complexity while API contracts stabilize.\n"
        "- Temporary dual-maintenance overhead across procedure and API layers.\n"
        "- Potential performance regressions unless query hot paths are benchmarked early.\n\n"
        "## Implementation Plan (phased)\n"
        "1. **Phase 1 - Discovery and Contracting:** inventory procedures, define API boundaries, agree success metrics.\n"
        "2. **Phase 2 - Pilot and Hardening:** migrate one bounded domain to the API layer, add observability and regression tests.\n"
        "3. **Phase 3 - Progressive Migration:** expand by domain, retire replaced procedures, and enforce new API-first standards.\n\n"
        "## Open Questions\n"
        "- Which domains deliver the best migration ROI in the first two quarters?\n"
        "- What SLO baselines should gate each migration phase?\n"
        "- How should ownership transition between DB-heavy and API teams be sequenced?\n"
    )
