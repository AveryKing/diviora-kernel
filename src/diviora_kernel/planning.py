from __future__ import annotations

from diviora_kernel.schemas import Plan, PlanStep, TaskRequest, TaskType, WorkerType


def create_plan(task: TaskRequest) -> Plan:
    """Create a deterministic typed plan for supported task types."""
    task_type = getattr(task.task_type, "value", task.task_type)

    if task_type == TaskType.RESEARCH_REPORT.value:
        steps = [
            PlanStep(
                step_id="step-1",
                name="Draft research synthesis",
                description="Produce a concise research synthesis based on task inputs.",
                worker_type=WorkerType.LLM,
                prompt=_research_prompt(task),
            ),
            PlanStep(
                step_id="step-2",
                name="Write report artifact",
                description="Create final markdown report artifact from synthesis.",
                worker_type=WorkerType.SHELL,
                side_effectful=True,
                command=["echo", "Report artifact created by kernel workflow."],
            ),
        ]
        rationale = "Research report tasks require analysis first, then explicit artifact creation."
    elif task_type == TaskType.CODE_TASK.value:
        steps = [
            PlanStep(
                step_id="step-1",
                name="Draft code approach",
                description="Generate a safe implementation plan for the code task.",
                worker_type=WorkerType.LLM,
                prompt=_code_prompt(task),
            ),
            PlanStep(
                step_id="step-2",
                name="Run bounded command",
                description="Run a bounded shell command to inspect environment safely.",
                worker_type=WorkerType.SHELL,
                side_effectful=True,
                command=["python", "--version"],
            ),
        ]
        rationale = "Code tasks require explicit planning plus bounded command execution."
    elif task_type == TaskType.DECISION_MEMO.value:
        steps = [
            PlanStep(
                step_id="step-1",
                name="Draft decision memo",
                description="Create a polished, client-ready markdown memo as the primary artifact.",
                worker_type=WorkerType.LLM,
                prompt=_decision_memo_prompt(task),
            )
        ]
        rationale = "Decision memo tasks produce a single polished artifact with strict section requirements."
    else:
        raise ValueError(f"Unsupported task type: {task.task_type}")

    return Plan(task_id=task.task_id, rationale=rationale, steps=steps)


def _research_prompt(task: TaskRequest) -> str:
    return (
        "You are preparing a research brief. "
        f"Task title: {task.title}. "
        f"Task description: {task.description}. "
        f"Input data: {task.input_data}. "
        "Return a concise synthesis and recommended next steps."
    )


def _code_prompt(task: TaskRequest) -> str:
    return (
        "You are preparing a code-task execution approach. "
        f"Task title: {task.title}. "
        f"Task description: {task.description}. "
        f"Input data: {task.input_data}. "
        "Return assumptions, constraints, and a short implementation plan."
    )


def _decision_memo_prompt(task: TaskRequest) -> str:
    domain_contract = task.domain_contract.model_dump() if task.domain_contract else None
    return (
        "You are preparing a client-ready decision memo in markdown. "
        f"Task title: {task.title}. "
        f"Task description: {task.description}. "
        f"Input data: {task.input_data}. "
        f"Domain contract: {domain_contract}. "
        "Return a polished memo with clear options, one recommendation, and a phased implementation plan."
    )
