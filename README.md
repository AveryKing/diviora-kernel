# diviora-kernel (v0)

Diviora Kernel is a contracts-first, human-in-the-loop, artifact-driven AI execution kernel.

## Design Principles

1. Human authority remains final.
2. Side effects are explicit.
3. Artifacts are first-class.
4. The kernel fails closed when uncertain.
5. Verification is separated from execution.
6. Runs end in explicit final states.

## v0 Architecture

- `schemas.py`: Canonical Pydantic contracts.
- `planning.py`: Typed plan creation from `TaskRequest`.
- `approvals.py`: Approval gating logic.
- `execution.py`: Run orchestration and worker dispatch.
- `workers/llm_worker.py`: Typed LLM worker.
- `workers/shell_worker.py`: Bounded shell worker with allowlist.
- `lanes/`: Deep-agent lane adapters that remain subordinate to kernel contracts.
- `verification.py`: Post-execution verification checks.
- `ledger.py`: Outcome and canonical run-record builder.
- `artifacts.py`: Filesystem artifact writing helpers.
- `cli.py`: Primary entrypoint.

## Canonical Concepts

- `TaskRequest`
- `Plan`
- `PlanStep`
- `ApprovalDecision`
- `StepResult`
- `VerificationResult`
- `RunOutcome`
- `RunRecord`

Final states:
`PASS`, `FAIL`, `BLOCKED`, `REFUSED`, `NEEDS_APPROVAL`, `PARTIAL`.

## Deep-Agent Worker Lanes

A **lane** is a bounded worker implementation that executes one `PlanStep` and must return a canonical `StepResult`.

Deep-agent lanes are integrated as adapters under `src/diviora_kernel/lanes/` and never replace kernel authority:

- Kernel contracts (`schemas.py`) remain canonical truth.
- Run ledger (`run_record.json`) remains canonical truth.
- Artifacts are explicit and inspectable.
- Lane-local runtime/memory is non-canonical and audit-only metadata.

Available deep-agent lanes:

- `ExecutiveDeepAgentWorker`: inspection/planning-oriented lane for artifacts like `proposed_plan.md`, decision framing, and status summaries.
- `ResearchDeepAgentWorker`: bounded research synthesis lane for artifacts like `research_notes.md`, option matrices, and recommendations.
- `CodingDeepAgentWorker`: bounded coding-planning lane for artifacts like `code_plan.md` and implementation notes; side-effectful steps still require kernel approval gating.

Each lane emits metadata in `StepResult.metadata` including `worker_id`, `worker_type`, `worker_runtime`, `execution_mode`, `requires_approval`, and `step_inputs`.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Usage

Auto approval (no pause):

```bash
diviora-kernel examples/code_task.json --run-dir runs
```

Manual approval (first run pauses):

```bash
diviora-kernel examples/research_task.json --run-dir runs
```

Manual approval provided:

```bash
diviora-kernel examples/research_task.json --run-dir runs \
  --approval-decision-file examples/approval_yes.json
```

## Output Artifacts

Each run writes an inspectable run folder containing:

- `task_request.json`
- `plan.json`
- `approval_decision.json` (if supplied)
- step artifacts (LLM, shell, and lane outputs)
- `verification.json`
- `final_outcome.json`
- `run_record.json`

## Extension Points

- Add new task types in `planning.py`.
- Add worker lanes under `workers/` or `lanes/`.
- Harden verification checks in `verification.py`.
- Replace deep-agent stub runtime with real `pydantic-deepagents` adapter in `lanes/deep_agent_base.py`.
