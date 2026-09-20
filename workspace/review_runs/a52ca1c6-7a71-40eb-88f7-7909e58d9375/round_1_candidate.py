from typing import Union

def div(a: Union[int, float], b: Union[int, float]) -> float:
    """Divides a by b, raising a ValueError if b is zero."""
    if b == 0:
        raise ValueError("The divisor 'b' cannot be zero.")
    return float(a / b)