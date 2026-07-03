"""Lightweight static checks for Milestone 1."""

DANGEROUS_PATTERNS = [
    "eval(",
    "exec(",
    "subprocess.run(",
    "subprocess.Popen(",
    "os.system(",
    "pickle.loads(",
    "yaml.load(",
]


def find_dangerous_patterns(code: str) -> list[str]:
    """Return simple dangerous pattern findings."""
    return [pattern for pattern in DANGEROUS_PATTERNS if pattern in code]
