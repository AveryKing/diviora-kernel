from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from diviora_kernel.execution import execute_run
from diviora_kernel.packs import build_pack, run_pack
from diviora_kernel.planning import create_plan
from diviora_kernel.schemas import ApprovalDecision, TaskRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diviora kernel v0 CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a single task request JSON")
    run_parser.add_argument("task_file", type=Path, help="Path to task request JSON")
    run_parser.add_argument("--run-dir", type=Path, default=Path("runs"), help="Base directory for run artifacts")
    run_parser.add_argument(
        "--approval-decision-file",
        type=Path,
        default=None,
        help="Optional path to approval decision JSON",
    )

    pack_parser = subparsers.add_parser("pack", help="Run a folder of task request JSON files")
    pack_parser.add_argument("pack_dir", type=Path, help="Path to pack folder containing task JSON files")
    pack_parser.add_argument("--run-dir", type=Path, default=Path("runs"), help="Base directory for pack artifacts")

    pack_build_parser = subparsers.add_parser("pack-build", help="Generate a task pack without execution")
    pack_build_parser.add_argument("goal", type=str, help="Natural language goal text")
    pack_build_parser.add_argument("--out", type=Path, required=True, help="Output pack directory")
    pack_build_parser.add_argument("--count", type=int, default=3, help="Maximum task count")
    pack_build_parser.add_argument("--force", action="store_true", help="Overwrite existing output directory")
    pack_build_parser.add_argument(
        "--force-clean",
        action="store_true",
        help="Delete partially generated output when validation fails",
    )

    args = parser.parse_args()
    if args.command is None:
        legacy = parser.parse_args(["run", *sys.argv[1:]])
        legacy.command = "run"
        return legacy
    return args


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if sys.version_info < (3, 11):
        print("Error: Python >= 3.11 is required.")
        raise SystemExit(2)

    args = parse_args()
    if args.command == "run":
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

    if args.command == "pack":
        code = run_pack(pack_dir=args.pack_dir, run_dir=args.run_dir)
        print(f"Pack exit code: {code}")
        return code

    if args.command == "pack-build":
        return build_pack(
            goal=args.goal,
            out_dir=args.out,
            count=args.count,
            force=args.force,
            force_clean=args.force_clean,
        )

    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
