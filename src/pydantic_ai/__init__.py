from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentRunResult:
    output: Any


class Agent:
    def __init__(self, model: Any, result_type: Any, system_prompt: str | None = None) -> None:
        self.model = model
        self.result_type = result_type
        self.system_prompt = system_prompt

    def run_sync(self, prompt: str) -> AgentRunResult:
        summary = f"Structured response for: {prompt[:80]}"
        details = "Deterministic local test-model output."
        return AgentRunResult(output=self.result_type(summary=summary, details=details))
