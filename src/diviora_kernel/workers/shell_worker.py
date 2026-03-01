from __future__ import annotations

import subprocess
from pathlib import Path

from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest
from diviora_kernel.workers.base import Worker


class ShellWorker(Worker):
    """Bounded shell worker with strict allowlist and no shell=True."""

    def __init__(self, allowlist: set[str] | None = None) -> None:
        self.allowlist = allowlist or {"echo", "python", "pytest"}

    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        if not step.command:
            return StepResult(
                step_id=step.step_id,
                success=False,
                status="failed",
                output_summary="No command provided",
                error="Shell step missing command",
                metadata={"worker": "shell"},
            )

        executable = step.command[0]
        if executable not in self.allowlist:
            return StepResult(
                step_id=step.step_id,
                success=False,
                status="blocked",
                output_summary=f"Command '{executable}' is not allowed",
                error="Command not in allowlist",
                metadata={"worker": "shell", "command": step.command},
            )

        completed = subprocess.run(
            step.command,
            cwd=str(run_dir),
            check=False,
            capture_output=True,
            text=True,
        )
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        artifact_path = run_dir / f"{step.step_id}_shell_output.txt"
        artifact_path.write_text(
            f"$ {' '.join(step.command)}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n",
            encoding="utf-8",
        )

        success = completed.returncode == 0
        return StepResult(
            step_id=step.step_id,
            success=success,
            status="completed" if success else "failed",
            output_summary=stdout or stderr or "No output",
            artifacts=[artifact_path.name],
            metadata={"worker": "shell", "returncode": completed.returncode},
            error=None if success else f"Command failed with return code {completed.returncode}",
        )
