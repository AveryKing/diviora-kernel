from __future__ import annotations

from diviora_kernel.schemas import ApprovalDecision


def requires_approval(step_side_effectful: bool, approval_mode: str) -> bool:
    return step_side_effectful and approval_mode == "manual"


def can_proceed(decision: ApprovalDecision | None) -> bool:
    return bool(decision and decision.approved)
