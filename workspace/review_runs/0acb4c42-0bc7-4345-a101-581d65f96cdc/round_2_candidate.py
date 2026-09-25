import math

def div(a: float, b: float) -> float:
    """Divides two numbers and raises ValueError if the divisor is zero."""
    if math.isclose(b, 0.0, abs_tol=1e-9):
        raise ValueError("The divisor 'b' cannot be zero.")
    return a / b