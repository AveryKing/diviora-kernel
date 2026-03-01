from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from diviora_kernel.schemas import PlanStep, StepResult, TaskRequest


class LaneWorker(ABC):
    """Kernel-compatible worker lane interface."""

    @property
    @abstractmethod
    def worker_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def worker_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def worker_runtime(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def execution_mode(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def side_effect_capable(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def execute(self, task: TaskRequest, step: PlanStep, run_dir: Path) -> StepResult:
        raise NotImplementedError
