from app.data.synthetic import generate_price_walk


def test_same_seed_produces_the_same_sequence():
    first = generate_price_walk(start_price=100.0, steps=20, seed=7)
    second = generate_price_walk(start_price=100.0, steps=20, seed=7)
    assert first == second


def test_different_seed_produces_a_different_sequence():
    first = generate_price_walk(start_price=100.0, steps=20, seed=7)
    second = generate_price_walk(start_price=100.0, steps=20, seed=8)
    assert first != second


def test_returns_the_requested_number_of_steps():
    walk = generate_price_walk(start_price=100.0, steps=15, seed=1)
    assert len(walk) == 15
