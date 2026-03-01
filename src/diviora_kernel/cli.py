from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from diviora_kernel.execution import execute_run
from diviora_kernel.planning import create_plan
from diviora_kernel.schemas import ApprovalDecision, TaskRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diviora kernel v0 CLI")
    parser.add_argument("task_file", type=Path, help="Path to task request JSON")
    parser.add_argument("--run-dir", type=Path, default=Path("runs"), help="Base directory for run artifacts")
    parser.add_argument(
        "--approval-decision-file",
        type=Path,
        default=None,
        help="Optional path to approval decision JSON",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if sys.version_info < (3, 11):
        print("Error: Python >= 3.11 is required.")
        raise SystemExit(2)

    args = parse_args()
    task = TaskRequest.model_validate(load_json(args.task_file))
    plan = create_plan(task)

    decision = None
    if args.approval_decision_file:
        decision = ApprovalDecision.model_validate(load_json(args.approval_decision_file))

    record = execute_run(task=task, plan=plan, base_run_dir=args.run_dir, approval_decision=decision)
    print(f"Run ID: {record.run_id}")
    print(f"Final state: {record.outcome.final_state}")
    print(f"Summary: {record.outcome.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
