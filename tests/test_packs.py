from __future__ import annotations

import json
from pathlib import Path

from diviora_kernel.packs import build_pack, run_pack


def _decision_task(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "title": f"Decision memo {task_id}",
        "description": "Decide between options",
        "task_type": "decision_memo",
        "approval_mode": "manual",
        "requested_by": "tests",
        "input_data": {"context": "test"},
    }


def test_pack_runner_runs_two_tasks_and_writes_index(tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    (pack_dir / "01_task.json").write_text(json.dumps(_decision_task("task-1")), encoding="utf-8")
    (pack_dir / "02_task.json").write_text(json.dumps(_decision_task("task-2")), encoding="utf-8")

    runs_dir = tmp_path / "runs"
    code = run_pack(pack_dir=pack_dir, run_dir=runs_dir)

    assert code == 0
    pack_root = next(runs_dir.iterdir())
    assert (pack_root / "01_01_task").exists()
    assert (pack_root / "02_02_task").exists()
    assert (pack_root / "index.md").exists()


def test_pack_build_validates_success_with_stubbed_executive_worker(tmp_path: Path) -> None:
    out_dir = tmp_path / "generated-pack"

    class StubExecutive:
        def generate_pack_artifacts(self, *, goal: str, count: int, pack_dir: Path):
            manifest = {
                "name": "pack_stub",
                "created_at": "2025-01-01T00:00:00Z",
                "goal": goal,
                "tasks": [
                    {"file": "tasks/01_decision.json", "title": "Task 1", "task_type": "decision_memo"},
                ],
            }
            tasks = [
                {
                    "file": "tasks/01_decision.json",
                    "title": "Task 1",
                    "task_type": "decision_memo",
                    "payload": _decision_task("stub-1"),
                }
            ]
            return manifest, tasks

    code = build_pack(
        goal="Prepare a launch decision",
        out_dir=out_dir,
        count=3,
        force=False,
        force_clean=False,
        executive_worker=StubExecutive(),
    )

    assert code == 0
    assert (out_dir / "pack.json").exists()
    assert (out_dir / "tasks" / "01_decision.json").exists()


def test_pack_build_fails_closed_on_invalid_task_json(tmp_path: Path) -> None:
    out_dir = tmp_path / "invalid-pack"

    class InvalidStubExecutive:
        def generate_pack_artifacts(self, *, goal: str, count: int, pack_dir: Path):
            manifest = {
                "name": "pack_invalid",
                "created_at": "2025-01-01T00:00:00Z",
                "goal": goal,
                "tasks": [
                    {"file": "tasks/01_invalid.json", "title": "Task 1", "task_type": "decision_memo"},
                ],
            }
            tasks = [
                {
                    "file": "tasks/01_invalid.json",
                    "title": "Task 1",
                    "task_type": "decision_memo",
                    "payload": {"task_id": "bad"},
                }
            ]
            return manifest, tasks

    code = build_pack(
        goal="Prepare a launch decision",
        out_dir=out_dir,
        count=3,
        force=False,
        force_clean=False,
        executive_worker=InvalidStubExecutive(),
    )

    assert code == 1
    assert out_dir.exists()
