# KERNEL_PACKS_AND_PACKBUILD_REPORT

## Objective
Implement pack-oriented operations in `diviora-kernel`:
1. Pack runner: execute multiple TaskRequest JSON files in one sequential, auditable bundle.
2. Pack build (Option D): generate validated pack artifacts from natural-language goals using the executive lane, without executing tasks.

## Pack runner behavior + folder layout
- New CLI command: `diviora-kernel pack <pack_dir> --run-dir runs`.
- Runner behavior:
  - Loads all `*.json` files in `pack_dir` (non-recursive), sorted by filename.
  - Creates `runs/pack_<timestamp>/` as the bundle root.
  - Executes each task sequentially through the existing kernel run flow.
  - Writes each task run to `runs/pack_<timestamp>/NN_<stem>/`.
  - Produces `runs/pack_<timestamp>/index.md` with task title, final state, and a link to primary artifact.
- Exit behavior:
  - Returns exit code `1` if any task final state is `FAIL`.
  - Returns exit code `0` otherwise.

## Pack build behavior + schemas
- New CLI command:
  - `diviora-kernel pack-build "<goal text>" --out <pack_dir> [--count N] [--force] [--force-clean]`
- Safety and creation behavior:
  - Refuses to write into existing output directory unless `--force` is set.
  - Uses the executive lane worker to generate auditable planning notes and a proposed pack structure.
  - Writes:
    - `pack.json`
    - `tasks/NN_<slug>.json`
- Manifest schema (`pack.json`) is validated as:
  - `name: string`
  - `created_at: iso datetime`
  - `goal: string`
  - `tasks: [{ file, title, task_type }]`
- Every generated task file is validated against canonical `TaskRequest` schema.

## Safety boundaries (no execution during build)
- `pack-build` only generates files; it does not call run execution.
- All generated TaskRequests default to `approval_mode: manual` for fail-closed posture.
- Executive lane artifacts remain non-canonical; kernel schemas and validation remain canonical truth.

## Validation rules
- Manifest must conform to `PackManifest` schema.
- Each task file must conform to `TaskRequest` schema.
- On validation failure:
  - Exit non-zero.
  - If `--force-clean` is supplied, partially created output directory is removed.
  - Otherwise artifacts are left on disk for inspection.

## Tests run + results
- Added tests for pack runner:
  - two decision memo tasks in a temp pack directory
  - verifies pack root, per-task subfolders, `index.md`, and success exit code
- Added tests for pack build:
  - deterministic stub worker generates valid manifest/tasks and passes validation
  - invalid task payload fails closed with non-zero return code

## Limitations + next steps (future interactive chat UI)
- Current pack build uses deterministic lane-assisted task drafting for predictable v0 behavior.
- Future enhancement: interactive executive chat workflow to iteratively refine generated packs before approval/execution.
- Future enhancement: richer primary artifact mapping by task subtype and lane metadata.
