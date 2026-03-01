# KERNEL CI and Operator Guardrails Report

## Objective

Make `diviora-kernel` reliably runnable and verifiable on any machine by adding:

- automated CI checks,
- Python-version guardrails at CLI entry,
- a single operator-friendly standard command flow.

## What Changed

1. Added GitHub Actions CI at `.github/workflows/ci.yml`.
2. Added a Python 3.11 guardrail in `src/diviora_kernel/cli.py` before argument parsing and task execution.
3. Added guardrail unit test coverage in `tests/test_cli.py`.
4. Consolidated runtime guidance into a single **Standard Operator Flow** section in `README.md`.

## CI Details

Workflow file: `.github/workflows/ci.yml`

- Triggers: `push`, `pull_request`
- Runner: `ubuntu-latest`
- Python version: `3.11` (matrix with one entry)
- Cache: `actions/setup-python` pip caching enabled
- Install commands:
  - `python -m pip install -U pip`
  - `python -m pip install -e ".[dev]"`
- Test command:
  - `python -m pytest -q`
- Fail-fast behavior is enabled at strategy level (`fail-fast: true`).

## Python Guardrail Behavior

At CLI startup, before argument parsing or run execution:

- If `sys.version_info < (3, 11)`, the CLI prints:
  - `Error: Python >= 3.11 is required.`
- Then exits with status code `2`.

This prevents partial execution on unsupported runtimes and provides a concise operator message.

## Tests Run

- `python -m pytest -q`

Includes a dedicated test that monkeypatches `sys.version_info` to `3.10.x` and verifies:

- exit code `2`,
- guardrail error message,
- argument parsing is not invoked.

## Limitations / Next Steps

- CI currently validates only Python 3.11 by design; if future compatibility needs expand, add 3.12+ matrix entries.
- Guardrail is implemented at CLI entrypoint and does not affect direct internal module imports (intentional for minimal/no-semantic-change scope).
- No lane runtime logic or kernel semantics were modified in this pass.
