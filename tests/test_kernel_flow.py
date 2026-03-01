from pathlib import Path

from diviora_kernel.execution import execute_run
from diviora_kernel.planning import create_plan
from diviora_kernel.schemas import ApprovalDecision, FinalState, PlanStep, StepResult, TaskRequest, TaskType, WorkerType
from diviora_kernel.verification import verify_run
from diviora_kernel.workers.shell_worker import ShellWorker


def test_plan_creation_for_supported_types() -> None:
    task = TaskRequest(
        task_id="t1",
        title="Research",
        description="Do research",
        task_type=TaskType.RESEARCH_REPORT,
        approval_mode="manual",
    )
    plan = create_plan(task)
    assert len(plan.steps) == 2
    assert plan.steps[0].worker_type == WorkerType.LLM


def test_decision_memo_plan_creates_single_primary_artifact_expectation() -> None:
    task = TaskRequest(
        task_id="dm-plan-1",
        title="Decision memo",
        description="Need options and recommendation",
        task_type=TaskType.DECISION_MEMO,
        approval_mode="auto",
    )

    plan = create_plan(task)

    assert 1 <= len(plan.steps) <= 6
    assert len(plan.steps) == 1
    assert plan.steps[0].worker_type == WorkerType.LLM
    assert "primary artifact" in plan.steps[0].description.lower()


def test_manual_approval_blocks_side_effect_step(tmp_path: Path) -> None:
    task = TaskRequest(
        task_id="t2",
        title="Manual test",
        description="Needs approval",
        task_type=TaskType.CODE_TASK,
        approval_mode="manual",
    )
    plan = create_plan(task)
    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path)

    assert record.outcome.final_state == FinalState.NEEDS_APPROVAL
    assert len(record.step_results) == 1


def test_auto_mode_executes_and_writes_outputs(tmp_path: Path) -> None:
    task = TaskRequest(
        task_id="t3",
        title="Auto test",
        description="Run steps",
        task_type=TaskType.CODE_TASK,
        approval_mode="auto",
    )
    plan = create_plan(task)
    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path)

    assert record.outcome.final_state == FinalState.PASS
    run_dirs = list(tmp_path.iterdir())
    assert run_dirs
    assert (run_dirs[0] / "run_record.json").exists()
    assert (run_dirs[0] / "verification.json").exists()


def test_decision_memo_run_produces_markdown_artifact(tmp_path: Path) -> None:
    task = TaskRequest(
        task_id="dm-run-1",
        title="API layer memo",
        description="Options + risks for API layer",
        task_type=TaskType.DECISION_MEMO,
        approval_mode="auto",
    )

    plan = create_plan(task)
    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path)

    assert record.outcome.final_state == FinalState.PASS
    run_dir = next(tmp_path.iterdir())
    assert (run_dir / "decision_memo.md").exists()


def test_shell_worker_blocks_disallowed_command(tmp_path: Path) -> None:
    worker = ShellWorker(allowlist={"echo"})
    task = TaskRequest(
        task_id="t4",
        title="Shell",
        description="No rm",
        task_type=TaskType.CODE_TASK,
        approval_mode="auto",
    )
    step = PlanStep(
        step_id="s1",
        name="Bad command",
        description="attempt blocked command",
        worker_type=WorkerType.SHELL,
        side_effectful=True,
        command=["rm", "-rf", "/tmp/nope"],
    )
    result = worker.execute(task, step, tmp_path)
    verification = verify_run(
        plan=create_plan(task).model_copy(update={"steps": [step]}),
        step_results=[result],
    )

    assert result.success is False
    assert result.status == "blocked"
    assert verification.passed is False


def test_manual_approval_can_proceed(tmp_path: Path) -> None:
    task = TaskRequest(
        task_id="t5",
        title="Approved run",
        description="Executes after approval",
        task_type=TaskType.RESEARCH_REPORT,
        approval_mode="manual",
    )
    plan = create_plan(task)
    decision = ApprovalDecision(approved=True, reviewer="operator", reason="safe")
    record = execute_run(task=task, plan=plan, base_run_dir=tmp_path, approval_decision=decision)

    assert record.outcome.final_state == FinalState.PASS
    assert len(record.step_results) == 2


def test_decision_memo_verification_passes_for_valid_and_fails_for_missing_section() -> None:
    task = TaskRequest(
        task_id="dm-verify-1",
        title="Decision memo verify",
        description="Verify strict checks",
        task_type=TaskType.DECISION_MEMO,
        approval_mode="auto",
    )
    plan = create_plan(task)

    valid_memo = """
# Decision Memo

## Context
A context section.

## Options
- Option A
- Option B
- Option C

## Recommendation
- Option B

## Risks / Tradeoffs
- Some risk.

## Implementation Plan (phased)
1. Phase one.
2. Phase two.

## Open Questions
- Unresolved question.
""".strip()

    valid_result = StepResult(
        step_id="step-1",
        success=True,
        status="completed",
        output_summary="ok",
        artifacts=["decision_memo.md"],
        metadata={"memo_content": valid_memo},
    )
    passed = verify_run(plan=plan, step_results=[valid_result], task=task)
    assert passed.passed is True

    invalid_memo = valid_memo.replace("## Implementation Plan (phased)\n1. Phase one.\n2. Phase two.\n\n", "")
    invalid_result = valid_result.model_copy(update={"metadata": {"memo_content": invalid_memo}})
    failed = verify_run(plan=plan, step_results=[invalid_result], task=task)
    assert failed.passed is False
    assert any("Implementation Plan (phased)" in warning for warning in failed.warnings)
