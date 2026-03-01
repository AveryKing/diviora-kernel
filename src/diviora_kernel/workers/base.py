from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest


class Worker(ABC):
    @abstractmethod
    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        raise NotImplementedError
