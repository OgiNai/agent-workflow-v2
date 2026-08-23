"""Requirements and policies passed with payload to _run_structured"""

INSPECTION_REQUIREMENTS = [
    "Inspect the candidate code only.",
    "Do not rewrite the full code.",
    "Return concrete findings, not generic advice.",
]

CODE_WRITER_REQUIREMENTS = [
    "Return complete Python code in the code field.",
    "Do not wrap code in markdown fences.",
    "Prefer type hints and clear errors.",
    "Do not introduce external dependencies unless required by the instruction.",
]

TEST_GENERATOR_REQUIREMENTS = [
    "Use pytest.",
    "Assume candidate code is stored in solution.py.",
    "Import from solution, e.g. from solution import function_name.",
    "Do not include markdown fences.",
]

EVALUATOR_DECISION_POLICY = {
    "pass": (
        "Use when no blocking correctness or security issues remain "
        "and required tests pass."
    ),
    "pass_with_warnings": (
        "Use when no blocking issues remain, but non-critical "
        "recommendations still exist."
    ),
    "retry": (
        "Use whenever blocking correctness, security, execution, or test issues remain."
    ),
}
