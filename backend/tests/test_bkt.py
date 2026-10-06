import pytest

from app.engine.bkt import BKTParams, bkt_update

P = BKTParams(p_init=0.3, p_transit=0.15, p_slip=0.1, p_guess=0.2)


def test_correct_worked_example():
    assert bkt_update(0.3, True, P) == pytest.approx(0.709756, abs=1e-5)


def test_wrong_worked_example():
    assert bkt_update(0.3, False, P) == pytest.approx(0.193220, abs=1e-5)


def test_correct_raises_wrong_lowers():
    assert bkt_update(0.5, False, P) < 0.5 < bkt_update(0.5, True, P)


def test_many_correct_approaches_one_but_stays_valid():
    p = 0.3
    for _ in range(10):
        p = bkt_update(p, True, P)
    assert 0.99 < p < 1


def test_alternating_answers_stay_in_open_interval():
    p = 0.3
    for i in range(200):
        p = bkt_update(p, i % 2 == 0, P)
        assert 0 < p < 1


def test_invalid_params_rejected():
    with pytest.raises(ValueError):
        BKTParams(p_slip=0)
    with pytest.raises(ValueError):
        BKTParams(p_slip=0.6, p_guess=0.5)


def test_foundational_concepts_start_higher():
    from app.engine.bkt import params_for
    assert params_for("vectors").p_init == 0.5
    assert params_for("incline").p_init == 0.3
