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
- `workers/llm_worker.py`: Typed LLM lane via PydanticAI.
- `workers/shell_worker.py`: Bounded shell lane with allowlist.
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
- step artifacts (LLM and shell outputs)
- `verification.json`
- `final_outcome.json`
- `run_record.json`

## Extension Points

- Add new task types in `planning.py`.
- Add worker lanes under `workers/`.
- Harden verification checks in `verification.py`.
- Replace test LLM model with production model in `llm_worker.py`.
