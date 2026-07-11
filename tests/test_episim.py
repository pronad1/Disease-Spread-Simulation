import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pytest

from episim import (
    run_scenario,
    simulate_seir,
    simulate_seird,
    compute_daily_incidence,
    compute_rt,
    herd_immunity_threshold,
    compute_doubling_time,
    compute_serial_interval,
    compute_cfr,
)


# ---------------------------------------------------------------------------
# Original tests (must stay passing)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New tests for derived epidemiological quantities
# ---------------------------------------------------------------------------

def test_daily_incidence_non_negative():
    """Daily incidence must always be >= 0."""
    times, states = simulate_seird(
        population=1000, beta=0.3, sigma=0.2, gamma=0.1, mu=0.005,
        initial_infected=10, days=60,
    )
    incidence = compute_daily_incidence(times, states)
    assert len(incidence) == len(times)
    assert np.all(incidence >= 0), "Incidence should never be negative"


def test_daily_incidence_sums_to_approx_attack_rate():
    """Cumulative incidence ≈ total infected (R + D at end)."""
    times, states = simulate_seird(
        population=1000, beta=0.3, sigma=0.2, gamma=0.1, mu=0.005,
        initial_infected=10, days=120,
    )
    incidence = compute_daily_incidence(times, states)
    total_infected_from_incidence = np.sum(incidence)
    final_R = states[-1, 3]
    final_D = states[-1, 4]
    total_infected_from_state = final_R + final_D
    # Should be within 5% of each other
    rel_error = abs(total_infected_from_incidence - total_infected_from_state) / (total_infected_from_state + 1)
    assert rel_error < 0.1, f"Cumulative incidence {total_infected_from_incidence:.0f} vs R+D {total_infected_from_state:.0f}"


def test_rt_starts_near_r0():
    """At time 0 (almost all susceptible), Rt should be very close to R₀."""
    beta, gamma, mu = 0.3, 0.1, 0.005
    times, states = simulate_seird(
        population=10_000, beta=beta, sigma=0.2, gamma=gamma, mu=mu,
        initial_infected=10, days=60,
    )
    rt = compute_rt(times, states, 10_000, beta, gamma, mu)
    r0_expected = beta / (gamma + mu)
    # At t=0 almost everyone is susceptible, so Rt ≈ R₀
    assert abs(rt[0] - r0_expected) < 0.05, f"Rt[0]={rt[0]:.3f} vs R₀={r0_expected:.3f}"


def test_rt_decreases_over_epidemic():
    """Rt should generally trend downward as S decreases."""
    beta, gamma, mu = 0.4, 0.1, 0.005
    times, states = simulate_seird(
        population=5000, beta=beta, sigma=0.2, gamma=gamma, mu=mu,
        initial_infected=10, days=120,
    )
    rt = compute_rt(times, states, 5000, beta, gamma, mu)
    # Rt at end should be well below Rt at start
    assert rt[-1] < rt[0], "Rt should fall as epidemic progresses"


def test_herd_immunity_threshold():
    """HIT = 1 - 1/R₀."""
    assert herd_immunity_threshold(2.0) == pytest.approx(0.5, abs=1e-9)
    assert herd_immunity_threshold(4.0) == pytest.approx(0.75, abs=1e-9)
    assert herd_immunity_threshold(1.0) == 0.0   # no threshold when R₀=1
    assert herd_immunity_threshold(0.5) == 0.0   # no threshold when R₀<1


def test_doubling_time_positive():
    """Doubling time should be positive and finite for epidemic growth scenario."""
    times, states = simulate_seird(
        population=10_000, beta=0.4, sigma=0.2, gamma=0.1, mu=0.005,
        initial_infected=10, days=60,
    )
    dt = compute_doubling_time(times, states)
    assert dt > 0, "Doubling time must be positive"
    assert dt < 100, "Doubling time should be reasonable (< 100 days here)"


def test_serial_interval():
    """Serial interval = 1/σ + 0.5/γ."""
    si = compute_serial_interval(sigma=0.2, gamma=0.1)
    expected = 1.0 / 0.2 + 0.5 / 0.1  # 5 + 5 = 10
    assert si == pytest.approx(expected, abs=1e-9)


def test_cfr():
    """CFR = mu / (mu + gamma)."""
    cfr = compute_cfr(mu=0.01, gamma=0.09)
    assert cfr == pytest.approx(0.1, abs=1e-9)
    assert compute_cfr(mu=0.0, gamma=0.1) == 0.0


def test_run_scenario_includes_derived_quantities():
    """run_scenario must now return all derived epidemiological quantities."""
    res = run_scenario(
        population=5000, beta=0.3, sigma=0.2, gamma=0.1, mu=0.005,
        initial_infected=10, days=60,
    )
    required_keys = [
        "incidence", "rt_series", "herd_immunity_threshold",
        "doubling_time", "serial_interval", "cfr", "attack_rate",
    ]
    for key in required_keys:
        assert key in res, f"run_scenario missing key: {key}"

    assert len(res["incidence"]) == 61
    assert len(res["rt_series"]) == 61
    assert 0.0 <= res["herd_immunity_threshold"] <= 1.0
    assert res["cfr"] >= 0.0
    assert res["serial_interval"] > 0.0
