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

Deep-agent lanes now use the real `pydantic-deep` runtime (`pydantic_deep`) under kernel authority:

- Kernel contracts (`schemas.py`) remain canonical truth.
- Run ledger (`run_record.json`) remains canonical truth.
- Artifacts are explicit and inspectable.
- Lane-local runtime/memory is non-canonical and written as `*_lane_memory.md` audit artifacts.

Bounding rules for all deep-agent lanes:

- Backend is rooted to the current `run_dir` only.
- Shell execution is disabled by default.
- Filesystem tools are disabled by default in v0 lane mode.
- Any side-effectful step still goes through kernel approval mapping (`approval_mode=manual` requires explicit approval).

Available deep-agent lanes:

- `ExecutiveDeepAgentWorker`: inspection-only lane for `proposed_plan.md`.
- `ResearchDeepAgentWorker`: research lane for `research_notes.md`.
- `CodingDeepAgentWorker`: coding-planning lane for `code_plan.md`.

Each lane emits metadata in `StepResult.metadata` including `worker_id`, `worker_type`, `worker_runtime`, `execution_mode`, `requires_approval`, and `step_inputs`.

## Standard Operator Flow

> Python **3.11+** is required for local runs and CI.

1. **Install**

```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

2. **Run examples**

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

3. **Inspect artifacts**

Artifacts are written under the selected run directory (for example `runs/<run_id>/`), including:

- `task_request.json`
- `plan.json`
- `approval_decision.json` (if supplied)
- step artifacts (LLM, shell, and lane outputs)
- lane memory artifacts (`*_lane_memory.md`)
- `verification.json`
- `final_outcome.json`
- `run_record.json`

4. **Run tests**

```bash
python -m pytest -q
```

## Extension Points

- Add new task types in `planning.py`.
- Add worker lanes under `workers/` or `lanes/`.
- Harden verification checks in `verification.py`.
- Extend deep-agent tooling only with explicit kernel approval mappings.
