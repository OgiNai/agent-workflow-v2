# Evaluation Benchmarks

This directory contains the reproducible benchmark corpus for the AI code
review and refactoring workflow.

## Purpose

Benchmark cases measure the quality of the system itself.

They are not a replacement for evaluating individual production requests.

Each benchmark case contains:

- a user instruction;
- source code;
- expected findings;
- expected behavior;
- security expectations;
- test expectations.

Cases are executed through the normal `CodeWorkflow`.

This allows different versions of the system to be compared using the same
inputs and expectations.

## Running the benchmark

The benchmark is intentionally separate from the normal pytest suite because
executing it invokes the LLM workflow.

Run it explicitly with:

```bash
uv run python -m apps.evals.benchmark_runner