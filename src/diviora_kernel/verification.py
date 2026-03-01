from __future__ import annotations

from diviora_kernel.schemas import Plan, StepResult, TaskRequest, TaskType, VerificationResult


_REQUIRED_DECISION_MEMO_SECTIONS = [
    "Context",
    "Options",
    "Recommendation",
    "Risks / Tradeoffs",
    "Implementation Plan (phased)",
    "Open Questions",
]


def verify_run(
    plan: Plan,
    step_results: list[StepResult],
    task: TaskRequest | None = None,
) -> VerificationResult:
    checks: list[str] = []
    warnings: list[str] = []

    planned_ids = {step.step_id for step in plan.steps}
    result_ids = {result.step_id for result in step_results}

    missing = sorted(planned_ids - result_ids)
    if missing:
        warnings.append(f"Missing results for steps: {', '.join(missing)}")
    else:
        checks.append("Every planned step has a recorded result")

    failed = [result.step_id for result in step_results if not result.success]
    if failed:
        warnings.append(f"Failed steps: {', '.join(failed)}")
    else:
        checks.append("All executed steps reported success")

    task_type = getattr(task.task_type, "value", task.task_type) if task else None
    if task_type == TaskType.DECISION_MEMO.value:
        decision_issues = _verify_decision_memo(step_results)
        if decision_issues:
            warnings.extend(decision_issues)
        else:
            checks.append("Decision memo passed strict section and recommendation checks")

    passed = not missing and not failed and not warnings
    return VerificationResult(passed=passed, checks=checks, warnings=warnings)


def _verify_decision_memo(step_results: list[StepResult]) -> list[str]:
    memo_text = ""
    for result in step_results:
        if "decision_memo.md" in result.artifacts:
            memo_text = str(result.metadata.get("memo_content", ""))
            break

    if not memo_text:
        return ["Missing decision_memo.md artifact content"]

    issues: list[str] = []
    sections = _extract_sections(memo_text)

    for section in _REQUIRED_DECISION_MEMO_SECTIONS:
        if section not in sections:
            issues.append(f"Decision memo missing required section: {section}")

    options_body = sections.get("Options", "")
    option_lines = [line for line in options_body.splitlines() if line.strip().startswith("- ")]
    if len(option_lines) < 3:
        issues.append("Decision memo Options section must include at least 3 options")

    recommendation_body = sections.get("Recommendation", "")
    recommendation_lines = [line for line in recommendation_body.splitlines() if line.strip().startswith("- ")]
    if len(recommendation_lines) != 1:
        issues.append("Decision memo Recommendation must contain exactly one option")

    return issues


def _extract_sections(memo_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None

    for raw_line in memo_text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
            continue

        if current is not None:
            existing = sections[current]
            sections[current] = f"{existing}\n{raw_line}" if existing else raw_line

    return sections
