from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from diviora_kernel.approvals import can_proceed, requires_approval
from diviora_kernel.artifacts import create_run_dir, write_json
from diviora_kernel.ledger import create_outcome, create_run_record
from diviora_kernel.schemas import ApprovalDecision, FinalState, Plan, RunOutcome, RunRecord, StepResult, TaskRequest
from diviora_kernel.lanes.coding_lane import CodingDeepAgentWorker
from diviora_kernel.lanes.executive_lane import ExecutiveDeepAgentWorker
from diviora_kernel.lanes.research_lane import ResearchDeepAgentWorker
from diviora_kernel.verification import verify_run
from diviora_kernel.workers.llm_worker import LLMWorker
from diviora_kernel.workers.shell_worker import ShellWorker


def execute_run_in_dir(
    task: TaskRequest,
    plan: Plan,
    run_dir: Path,
    approval_decision: ApprovalDecision | None = None,
) -> RunRecord:
    run_id = str(uuid4())
    run_dir.mkdir(parents=True, exist_ok=True)
    step_results: list[StepResult] = []
    approval_mode = getattr(task.approval_mode, "value", task.approval_mode)

    workers = {
        "llm": LLMWorker(),
        "shell": ShellWorker(),
        "executive_deep_agent": ExecutiveDeepAgentWorker(),
        "research_deep_agent": ResearchDeepAgentWorker(),
        "coding_deep_agent": CodingDeepAgentWorker(),
    }

    for step in plan.steps:
        if requires_approval(step.side_effectful, approval_mode) and not can_proceed(approval_decision):
            outcome = RunOutcome(
                final_state=FinalState.NEEDS_APPROVAL,
                summary=f"Manual approval required before step '{step.step_id}'.",
                completed_steps=len([r for r in step_results if r.success]),
                failed_steps=len([r for r in step_results if not r.success]),
            )
            record = create_run_record(
                run_id=run_id,
                task_request=task,
                plan=plan,
                outcome=outcome,
                step_results=step_results,
                verification=None,
                approval_decision=approval_decision,
            )
            write_json(run_dir / "run_record.json", record.model_dump(mode="json"))
            write_json(run_dir / "final_outcome.json", outcome.model_dump(mode="json"))
            return record

        worker_type = getattr(step.worker_type, "value", step.worker_type)
        worker = workers[worker_type]
        result = worker.execute(task=task, step=step, run_dir=run_dir)
        step_results.append(result)

    verification = verify_run(plan=plan, step_results=step_results, task=task)
    outcome = create_outcome(verification=verification, step_results=step_results)
    record = create_run_record(
        run_id=run_id,
        task_request=task,
        plan=plan,
        outcome=outcome,
        step_results=step_results,
        verification=verification,
        approval_decision=approval_decision,
    )

    write_json(run_dir / "task_request.json", task.model_dump(mode="json"))
    write_json(run_dir / "plan.json", plan.model_dump(mode="json"))
    if approval_decision:
        write_json(run_dir / "approval_decision.json", approval_decision.model_dump(mode="json"))
    write_json(run_dir / "verification.json", verification.model_dump(mode="json"))
    write_json(run_dir / "final_outcome.json", outcome.model_dump(mode="json"))
    write_json(run_dir / "run_record.json", record.model_dump(mode="json"))

    return record


def execute_run(
    task: TaskRequest,
    plan: Plan,
    base_run_dir: Path,
    approval_decision: ApprovalDecision | None = None,
) -> RunRecord:
    run_dir = create_run_dir(base_run_dir, task.task_id)
    return execute_run_in_dir(task=task, plan=plan, run_dir=run_dir, approval_decision=approval_decision)
