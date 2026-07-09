import sys
from pathlib import Path

# Allow running this file directly: python tests/test_episim.py
# conftest.py handles the sys.path for pytest runs
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np

from episim import run_scenario, simulate_seir


def test_seir_conservation_and_shape():
    initial_infected = 10
    times, states = simulate_seir(
        population=1000,
        beta=0.3,
        sigma=0.2,
        gamma=0.1,
        initial_infected=initial_infected,
        days=60,
    )

    assert len(times) == 61
    assert states.shape == (61, 4)

    susceptible, exposed, infectious, recovered = states.T
    total = susceptible + exposed + infectious + recovered
    assert np.allclose(total, 1000)
    assert np.max(infectious) > initial_infected


def test_intervention_reduces_peak_infections():
    baseline = run_scenario(
        population=1000,
        beta=0.3,
        sigma=0.2,
        gamma=0.1,
        initial_infected=10,
        days=60,
        vaccine_coverage=0.0,
        distancing_reduction=0.0,
    )

    intervention = run_scenario(
        population=1000,
        beta=0.3,
        sigma=0.2,
        gamma=0.1,
        initial_infected=10,
        days=60,
        vaccine_coverage=0.2,
        distancing_reduction=0.3,
    )

    assert intervention["peak_infected"] < baseline["peak_infected"]
    assert intervention["final_recovered"] < baseline["final_recovered"]


def test_all_epidemic_models():
    for m in ["SEIRD", "SEIR", "SIR", "SIS"]:
        res = run_scenario(
            population=1000,
            beta=0.3,
            sigma=0.2,
            gamma=0.1,
            mu=0.01,
            initial_infected=10,
            days=30,
            model_type=m,
        )
        assert res["states"].shape[0] == 31
        assert "times" in res
        assert "r0" in res
        assert "peak_infected" in res
        # Check conservation of total population
        total_pop = np.sum(res["states"], axis=1)
        assert np.allclose(total_pop, 1000)
