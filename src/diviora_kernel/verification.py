from __future__ import annotations

from diviora_kernel.schemas import Plan, StepResult, VerificationResult


def verify_run(plan: Plan, step_results: list[StepResult]) -> VerificationResult:
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

    passed = not missing and not failed
    return VerificationResult(passed=passed, checks=checks, warnings=warnings)
