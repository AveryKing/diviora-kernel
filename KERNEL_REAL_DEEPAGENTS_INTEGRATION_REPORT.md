# KERNEL REAL DEEPAGENTS INTEGRATION REPORT

## Objective
Replace offline compatibility shims with real runtime dependencies and wire deep-agent lanes to real `pydantic-deep` while preserving kernel authority, approval semantics, and canonical contracts.

## What changed
- Removed shim packages that shadowed real dependencies.
- Updated project dependencies to use real `pydantic`, `pydantic-ai`, and `pydantic-deep`.
- Reworked deep-agent lane adapter to call `pydantic_deep.create_deep_agent` and `pydantic_deep.create_default_deps`.
- Implemented bounded deep-agent runtime setup per run directory with shell execution disabled.
- Standardized lane outputs into canonical `StepResult` with explicit artifacts and audit metadata.
- Added lane memory artifact output (`*_lane_memory.md`) marked non-canonical.
- Updated tests for real runtime metadata and bounded behavior assertions.
- Updated README with current installation and runtime behavior.

## Dependencies added
- `pydantic>=2`
- `pydantic-ai`
- `pydantic-deep`

## Shims removed
- `src/pydantic/`
- `src/pydantic_ai/`
- `src/pydantic_ai/models/`

## How deep-agent lanes are bounded
- Each lane creates a `LocalBackend` rooted at the current kernel `run_dir`.
- Allowed directories are restricted to `[run_dir]`.
- Command execution is disabled (`enable_execute=False` and `include_execute=False`).
- Filesystem tools are disabled by default (`include_filesystem=False`) for v0 fail-closed behavior.
- Memory features are disabled as runtime state and represented only in explicit audit artifacts.

## Approval mapping and allowed behavior
- Kernel remains canonical source for approval checks (`execution.py` gating before worker execution).
- Side-effectful coding steps with manual approval and no approval decision still return `NEEDS_APPROVAL`.
- Executive lane is inspection-only and reports `requires_approval: false`.
- Research lane is bounded to read/plan mode with shell disabled.
- Coding lane remains planning-first with no shell execution in v0 lane runtime.

## Tests run + results
- `pytest -q` — PASS

## Limitations and next steps
- Deep-agent lane currently runs in deterministic tool-disabled profile suitable for kernel-safe v0.
- Optional future enhancement: approved filesystem editing within run-dir for explicitly approved coding steps.
- Optional future enhancement: approval-mapped shell tool wrapper with allowlist and audit trail.
- Optional future enhancement: optional containerized sandbox integration (kept optional, not required for v0).
