from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from diviora_kernel.schemas import DomainContract, PlanStep, StepResult, TaskRequest, TaskType
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
    contract = task.domain_contract
    if contract:
        return _build_domain_contract_memo(topic, contract)
    return _build_default_memo(topic)


def _build_domain_contract_memo(topic: str, contract: DomainContract) -> str:
    option_fields = contract.option_required_fields or [
        "Who it's for",
        "What you deliver",
        "Pricing",
        "How you sell",
        "Why it wins",
    ]

    options = [
        {
            "name": "Option 1: ICP-specific fast start package",
            "values": {
                "Who it's for": "Founder-led service businesses with urgent lead generation needs.",
                "What you deliver": "A 14-day launch sprint including offer positioning, one conversion asset, and outreach scripts.",
                "Pricing": "$1,500 setup + $900/mo optimization.",
                "How you sell": "Direct founder outreach and warm intro calls with a same-week pilot kickoff.",
                "Why it wins": "Low friction entry point that proves value quickly.",
            },
        },
        {
            "name": "Option 2: Revenue acceleration retainer",
            "values": {
                "Who it's for": "B2B operators with an existing funnel but inconsistent conversion performance.",
                "What you deliver": "Monthly experimentation program across offer messaging, landing page, and close-rate playbooks.",
                "Pricing": "$3,000/mo with 90-day commitment.",
                "How you sell": "Pipeline audit workshop followed by fixed-scope implementation roadmap.",
                "Why it wins": "Higher contract value with repeatable delivery cadence.",
            },
        },
        {
            "name": "Option 3: Hybrid advisory + execution",
            "values": {
                "Who it's for": "Teams that need strategy guidance while keeping internal execution ownership.",
                "What you deliver": "Weekly strategy sessions, decision support, and campaign QA.",
                "Pricing": "$1,000/mo advisory or $2,400/mo with execution support.",
                "How you sell": "Diagnostic call to map bottlenecks and align on 30-day outcomes.",
                "Why it wins": "Flexible model that expands from advisory to delivery as trust grows.",
            },
        },
    ]

    option_lines: list[str] = []
    for option in options:
        option_lines.append(f"- **{option['name']}**")
        for field in option_fields:
            value = option["values"].get(field, f"Deterministic placeholder for {field}.")
            option_lines.append(f"  - {field}: {value}")

    recommendation_lines = [
        "- **Recommend Option 1** for fastest initial revenue capture with simple delivery.",
        "- Exact price points: $1,500 setup and $900/mo starting in month one.",
        "- This is easiest to sell in 30 days because the scope is concrete, the setup fee funds delivery immediately, and distribution can start from warm network intros.",
    ]

    rubric_text = ""
    if contract.rubric:
        rubric_lines = [f"- {key}: {value}" for key, value in contract.rubric.items()]
        rubric_text = "\n".join(rubric_lines)

    sections = contract.required_sections or [
        "Context",
        "Options",
        "Recommendation",
        "Risks / Tradeoffs",
        "Implementation Plan (phased)",
        "Open Questions",
    ]

    content_by_section = {
        "Context": (
            f"This memo evaluates {topic} for the {contract.domain_name} domain. "
            "The focus is on ICP clarity, offer design, pricing logic, and distribution paths that convert quickly."
        ),
        "Options": "\n".join(option_lines),
        "Recommendation": "\n".join(recommendation_lines),
        "Risks / Tradeoffs": "- Underpricing may increase demand but compress margins.\n- Over-scoping delivery can delay onboarding.\n- Distribution channels need a clear owner to avoid slow pipeline fill.",
        "Implementation Plan (phased)": "1. Week 1: finalize ICP and offer narrative.\n2. Week 2: publish offer page and outreach assets.\n3. Weeks 3-4: run distribution, close first clients, and capture pricing feedback.",
        "Open Questions": "- Which ICP segment has the shortest sales cycle?\n- Should the first distribution channel be referrals or outbound?\n- When should price points be raised after initial traction?",
    }

    assembled_sections: list[str] = []
    for section in sections:
        body = content_by_section.get(section, f"Domain requirement noted: {section}.")
        assembled_sections.append(f"## {section}\n{body}")

    return "# Decision Memo\n\n" + "\n\n".join(assembled_sections) + (f"\n\n## Domain Rubric\n{rubric_text}\n" if rubric_text else "\n")


def _build_default_memo(topic: str) -> str:
    return (
        "# Decision Memo\n\n"
        "## Context\n"
        f"This memo evaluates {topic} and frames practical choices for near-term execution.\n\n"
        "## Options\n"
        "- **Option 1: Minimal launch path.** Fast start with constrained scope and clear ownership.\n"
        "- **Option 2: Balanced rollout path.** Moderate scope with risk controls and measurable milestones.\n"
        "- **Option 3: Comprehensive build path.** Highest upside with the largest execution burden.\n\n"
        "## Recommendation\n"
        "- **Recommend Option 2** as the pragmatic path with delivery speed and manageable complexity.\n\n"
        "## Risks / Tradeoffs\n"
        "- Delivery can stall without explicit decision ownership.\n"
        "- Scope growth may reduce near-term execution velocity.\n"
        "- Team capacity must be protected against parallel priorities.\n\n"
        "## Implementation Plan (phased)\n"
        "1. **Phase 1 - Alignment:** finalize goals, constraints, and success metrics.\n"
        "2. **Phase 2 - Pilot:** execute a bounded pilot and collect feedback.\n"
        "3. **Phase 3 - Scale:** expand rollout with lessons from the pilot.\n\n"
        "## Open Questions\n"
        "- What is the minimum success threshold for the first cycle?\n"
        "- Which risks require active mitigation before scale?\n"
        "- What cadence should be used for executive decision checkpoints?\n"
    )
