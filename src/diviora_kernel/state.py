from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RunContext:
    run_id: str
    run_dir: Path
