from __future__ import annotations

from datetime import datetime, timezone

from diviora_kernel.schemas import (
    ApprovalDecision,
    FinalState,
    Plan,
    RunOutcome,
    RunRecord,
    StepResult,
    TaskRequest,
    VerificationResult,
)


def create_outcome(verification: VerificationResult, step_results: list[StepResult]) -> RunOutcome:
    completed = sum(1 for result in step_results if result.success)
    failed = sum(1 for result in step_results if not result.success)

    if verification.passed:
        state = FinalState.PASS
        summary = "Run passed verification checks."
    elif completed > 0 and failed > 0:
        state = FinalState.PARTIAL
        summary = "Run partially completed with one or more failures."
    elif failed > 0:
        state = FinalState.FAIL
        summary = "Run failed verification checks."
    else:
        state = FinalState.BLOCKED
        summary = "Run blocked before execution completed."

    return RunOutcome(final_state=state, summary=summary, completed_steps=completed, failed_steps=failed)


def create_run_record(
    run_id: str,
    task_request: TaskRequest,
    plan: Plan,
    outcome: RunOutcome,
    step_results: list[StepResult],
    verification: VerificationResult | None,
    approval_decision: ApprovalDecision | None,
) -> RunRecord:
    now = datetime.now(timezone.utc)
    return RunRecord(
        run_id=run_id,
        task_request=task_request,
        plan=plan,
        approval_decision=approval_decision,
        step_results=step_results,
        verification=verification,
        outcome=outcome,
        started_at=now,
        ended_at=now,
    )
