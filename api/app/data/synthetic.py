import random


def generate_price_walk(
    start_price: float, steps: int, seed: int = 7, step_size: float = 0.5
) -> list[float]:
    rng = random.Random(seed)
    prices = [round(start_price, 2)]
    for _ in range(steps - 1):
        change = rng.uniform(-step_size, step_size)
        prices.append(round(prices[-1] + change, 2))
    return prices
