def calculate_percentage(x: float, y: float) -> float:
    """
    Calculate the percentage of a value.

    Args:
        x (float): Value to calculate the percentage of.
        y (float): Percentage value.
    """
    return (x * y) / 100.0

def sats_to_msats(x: int):
    return round(x * 1000)
