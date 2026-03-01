from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from diviora_kernel.lanes.deep_agent_base import DeepAgentLaneWorker
from diviora_kernel.schemas import ApprovalMode, PlanStep, TaskRequest, TaskType


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

    def generate_pack_artifacts(self, *, goal: str, count: int, pack_dir: Path) -> tuple[dict, list[dict]]:
        pack_dir.mkdir(parents=True, exist_ok=True)
        task = TaskRequest(
            task_id="pack-build",
            title="Pack build request",
            description=goal,
            task_type=TaskType.DECISION_MEMO,
            approval_mode=ApprovalMode.MANUAL,
            input_data={"goal": goal, "count": count},
        )
        step = PlanStep(
            step_id="pack-spec",
            name="Generate pack specification",
            description="Produce an auditable pack-generation specification without executing tasks.",
            worker_type=self.worker_type,
        )
        artifact, lane_memory, _ = self._run_lane(task=task, step=step, run_dir=pack_dir)
        (pack_dir / "pack_generation_notes.md").write_text(artifact, encoding="utf-8")
        (pack_dir / "pack_generation_lane_memory.md").write_text(lane_memory, encoding="utf-8")

        task_types = [TaskType.DECISION_MEMO.value, TaskType.RESEARCH_REPORT.value, TaskType.CODE_TASK.value]
        tasks: list[dict] = []
        for idx in range(1, count + 1):
            task_type = task_types[(idx - 1) % len(task_types)]
            slug = self._slugify(f"{task_type}-{idx}")
            file_name = f"tasks/{idx:02d}_{slug}.json"
            tasks.append(
                {
                    "file": file_name,
                    "title": f"{goal[:80]} (Task {idx})",
                    "task_type": task_type,
                    "payload": {
                        "task_id": f"pack-{idx:02d}-{slug}",
                        "title": f"{goal[:80]}: task {idx}",
                        "description": f"Goal: {goal}\nTask {idx} of {count}. Produce a clear, auditable deliverable.",
                        "task_type": task_type,
                        "approval_mode": ApprovalMode.MANUAL.value,
                        "requested_by": "pack_build",
                        "input_data": {"goal": goal, "task_index": idx, "task_count": count},
                    },
                }
            )

        manifest = {
            "name": f"pack_{self._slugify(goal)[:40] or 'goal'}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "goal": goal,
            "tasks": [{"file": t["file"], "title": t["title"], "task_type": t["task_type"]} for t in tasks],
        }
        return manifest, tasks

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "task"
