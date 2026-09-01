from typing import Optional

def div(a: float, b: float) -> Optional[float]:
    """Divides a by b, returning None if b is zero."""
    if b == 0:
        return None
    return a / b