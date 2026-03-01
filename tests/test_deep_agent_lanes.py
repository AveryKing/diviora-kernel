from __future__ import annotations

import json
from pathlib import Path

from diviora_kernel.execution import execute_run
from diviora_kernel.schemas import FinalState, Plan, PlanStep, TaskRequest, TaskType, WorkerType


def _task(task_id: str, approval_mode: str = "auto") -> TaskRequest:
    return TaskRequest(
        task_id=task_id,
        title="Lane task",
        description="Validate deep-agent lane behavior",
        task_type=TaskType.CODE_TASK,
        approval_mode=approval_mode,
        input_data={"scope": "bounded"},
    )


def test_executive_lane_creates_proposed_plan_with_real_runtime(tmp_path: Path) -> None:
    task = _task("lane-exec")
    step = PlanStep(
        step_id="step-1",
        name="Executive planning",
        description="Create executive artifact",
        worker_type=WorkerType.EXECUTIVE_DEEP_AGENT,
    )
    plan = Plan(task_id=task.task_id, rationale="test", steps=[step])

    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path)

    assert record.outcome.final_state == FinalState.PASS
    assert len(record.step_results) == 1
    result = record.step_results[0]
    assert result.metadata["worker_type"] == "executive_deep_agent"
    assert result.metadata["execution_mode"] == "inspection"
    assert result.metadata["worker_runtime"] == "pydantic-deep"
    assert result.metadata["requires_approval"] is False
    assert "step_description" in result.metadata["step_inputs"]

    run_dir = next(tmp_path.iterdir())
    assert (run_dir / "step-1_proposed_plan.md").exists()


def test_research_lane_creates_notes_and_is_bounded_to_run_dir(tmp_path: Path) -> None:
    task = _task("lane-research")
    step = PlanStep(
        step_id="step-1",
        name="Research synthesis",
        description="Produce research notes",
        worker_type=WorkerType.RESEARCH_DEEP_AGENT,
    )
    plan = Plan(task_id=task.task_id, rationale="test", steps=[step])

    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path)

    assert record.outcome.final_state == FinalState.PASS
    result = record.step_results[0]
    assert result.success is True
    assert result.metadata["worker_runtime"] == "pydantic-deep"
    assert result.metadata["lane_metadata"]["inspection_only"] is True
    assert result.metadata["lane_metadata"]["shell_execution_enabled"] is False
    assert result.metadata["lane_metadata"]["backend_root"].startswith(str(tmp_path))

    run_dir = next(tmp_path.iterdir())
    assert (run_dir / "step-1_research_notes.md").exists()


def test_coding_lane_respects_kernel_approval_semantics(tmp_path: Path) -> None:
    task = _task("lane-coding", approval_mode="manual")
    step = PlanStep(
        step_id="step-1",
        name="Coding execution",
        description="Would be side effectful",
        worker_type=WorkerType.CODING_DEEP_AGENT,
        side_effectful=True,
    )
    plan = Plan(task_id=task.task_id, rationale="test", steps=[step])

    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path)

    assert record.outcome.final_state == FinalState.NEEDS_APPROVAL
    assert record.step_results == []


def test_lane_outputs_do_not_become_canonical_truth(tmp_path: Path) -> None:
    task = _task("lane-canonical")
    step = PlanStep(
        step_id="step-1",
        name="Executive planning",
        description="Create executive artifact",
        worker_type=WorkerType.EXECUTIVE_DEEP_AGENT,
    )
    plan = Plan(task_id=task.task_id, rationale="test", steps=[step])

    execute_run(task=task, plan=plan, base_run_dir=tmp_path)
    run_dir = next(tmp_path.iterdir())
    run_record = json.loads((run_dir / "run_record.json").read_text(encoding="utf-8"))
    metadata = run_record["step_results"][0]["metadata"]

    assert metadata["canonical_truth_source"] == "kernel_ledger"
    assert metadata["lane_memory_canonical"] is False


def test_lane_metadata_present_in_run_record(tmp_path: Path) -> None:
    task = _task("lane-metadata")
    step = PlanStep(
        step_id="step-1",
        name="Coding planning",
        description="Generate implementation notes",
        worker_type=WorkerType.CODING_DEEP_AGENT,
        side_effectful=False,
    )
    plan = Plan(task_id=task.task_id, rationale="test", steps=[step])

    execute_run(task=task, plan=plan, base_run_dir=tmp_path)
    run_dir = next(tmp_path.iterdir())
    run_record = json.loads((run_dir / "run_record.json").read_text(encoding="utf-8"))
    metadata = run_record["step_results"][0]["metadata"]

    assert metadata["worker_id"] == "lane.coding.deep_agent.v1"
    assert metadata["requires_approval"] is False
    assert metadata["step_inputs"]["step_name"] == "Coding planning"
    assert metadata["step_inputs"]["task_context_summary"]
    assert (run_dir / "step-1_lane_memory.md").exists()
