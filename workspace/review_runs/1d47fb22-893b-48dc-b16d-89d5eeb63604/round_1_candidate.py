from typing import Union

def div(a: float, b: float) -> float:
    """Divides a by b, raising a ValueError if b is zero."""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return float(a / b)