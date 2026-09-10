from typing import Union

def calculate_average(total: Union[int, float], count: Union[int, float]) -> float:
    if count == 0:
        raise ValueError("Count cannot be zero when calculating an average.")
    return float(total / count)