from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from diviora_kernel.artifacts import write_json
from diviora_kernel.execution import execute_run_in_dir
from diviora_kernel.lanes.executive_lane import ExecutiveDeepAgentWorker
from diviora_kernel.planning import create_plan
from diviora_kernel.schemas import FinalState, PackManifest, TaskRequest


def run_pack(pack_dir: Path, run_dir: Path) -> int:
    task_files = sorted([path for path in pack_dir.glob("*.json") if path.is_file()])
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack_root = run_dir / f"pack_{timestamp}"
    pack_root.mkdir(parents=True, exist_ok=False)

    index_rows: list[str] = ["# Pack Run Index", "", f"Pack source: `{pack_dir}`", "", "| Task | State | Primary Artifact |", "| --- | --- | --- |"]
    has_fail = False

    for idx, task_file in enumerate(task_files, start=1):
        task = TaskRequest.model_validate(json.loads(task_file.read_text(encoding="utf-8")))
        plan = create_plan(task)
        task_run_dir = pack_root / f"{idx:02d}_{task_file.stem}"
        record = execute_run_in_dir(task=task, plan=plan, run_dir=task_run_dir)
        final_state = record.outcome.final_state
        if final_state == FinalState.FAIL:
            has_fail = True

        primary = _primary_artifact(task_type=getattr(task.task_type, "value", task.task_type), run_dir=task_run_dir)
        primary_link = f"[{primary}]({idx:02d}_{task_file.stem}/{primary})" if primary else "-"
        index_rows.append(f"| {task.title} | {final_state} | {primary_link} |")

    (pack_root / "index.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8")
    return 1 if has_fail else 0


def build_pack(
    *,
    goal: str,
    out_dir: Path,
    count: int,
    force: bool,
    force_clean: bool,
    executive_worker: ExecutiveDeepAgentWorker | None = None,
) -> int:
    if out_dir.exists():
        if not force:
            raise FileExistsError(f"Output directory already exists: {out_dir}")
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=False)
    worker = executive_worker or ExecutiveDeepAgentWorker()
    manifest_payload, generated_tasks = worker.generate_pack_artifacts(goal=goal, count=count, pack_dir=out_dir)

    tasks_dir = out_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    for task in generated_tasks:
        task_path = out_dir / task["file"]
        task_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(task_path, task["payload"])

    write_json(out_dir / "pack.json", manifest_payload)

    try:
        PackManifest.model_validate(json.loads((out_dir / "pack.json").read_text(encoding="utf-8")))
        for task in generated_tasks:
            TaskRequest.model_validate(json.loads((out_dir / task["file"]).read_text(encoding="utf-8")))
    except Exception:
        if force_clean:
            shutil.rmtree(out_dir, ignore_errors=True)
        return 1

    return 0


def _primary_artifact(task_type: str, run_dir: Path) -> str:
    if task_type == "decision_memo" and (run_dir / "decision_memo.md").exists():
        return "decision_memo.md"

    if task_type == "research_report":
        if (run_dir / "research_report.md").exists():
            return "research_report.md"
        return "final_outcome.json"

    return "final_outcome.json"
