"""
tests/test_seir.py
==================
Unit tests for the SEIRD model.

Critical invariants every epidemiological model must satisfy:
  1. Conservation: S + E + I + R + D = N at all timesteps
  2. Disease extinction: when R₀ < 1, epidemic always dies out
  3. Epidemic growth: when R₀ > 1, epidemic grows initially
  4. Boundary conditions: N=1000, I0=1 must work without errors
  5. Intervention effects: lockdown must reduce peak infected
"""

import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.seir_model import SEIRDModel, Intervention, sensitivity_analysis


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
BASE = dict(N=10_000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.01, nu=0.0, I0=1)


# ---------------------------------------------------------------------------
# Test 1: Population conservation
# ---------------------------------------------------------------------------
class TestConservation:
    def test_seird_conservation_no_intervention(self):
        """S + E + I + R + D must equal N at every timestep."""
        model = SEIRDModel(**BASE)
        df = model.run(days=200)
        total = df["S"] + df["E"] + df["I"] + df["R"] + df["D"]
        np.testing.assert_allclose(total, BASE["N"], rtol=1e-4,
                                   err_msg="Population not conserved!")

    def test_seird_conservation_with_lockdown(self):
        """Conservation must hold even with a time-varying intervention."""
        model = SEIRDModel(**BASE)
        interv = Intervention("Test lockdown", start_day=30, beta_reduction=0.50)
        df = model.run(days=200, intervention=interv)
        total = df["S"] + df["E"] + df["I"] + df["R"] + df["D"]
        np.testing.assert_allclose(total, BASE["N"], rtol=1e-4)

    def test_no_negative_compartments(self):
        """No compartment should go negative."""
        model = SEIRDModel(**BASE)
        df = model.run(days=365)
        for col in ["S", "E", "I", "R", "D"]:
            assert (df[col] >= -1e-6).all(), f"{col} went negative!"


# ---------------------------------------------------------------------------
# Test 2: R₀ < 1 → disease dies out
# ---------------------------------------------------------------------------
class TestReproductionNumber:
    def test_r0_less_than_1_disease_dies_out(self):
        """When R₀ < 1 (β < γ), infectious population must decline to near zero."""
        params = dict(N=10_000, beta=0.05, sigma=0.20, gamma=0.20, mu=0.0, nu=0.0, I0=10)
        model = SEIRDModel(**params)
        assert model.R0 < 1.0, f"Expected R₀ < 1, got {model.R0}"
        df = model.run(days=365)
        final_I = df["I"].iloc[-1]
        assert final_I < 10, f"Disease did not die out: I_final = {final_I:.2f}"

    def test_r0_greater_than_1_epidemic_grows(self):
        """When R₀ > 1, epidemic should grow from initial seed."""
        params = dict(N=100_000, beta=0.40, sigma=0.20, gamma=0.10, mu=0.0, nu=0.0, I0=1)
        model = SEIRDModel(**params)
        assert model.R0 > 1.0
        df = model.run(days=100)
        max_I = df["I"].max()
        assert max_I > 1, f"Epidemic did not grow: max_I = {max_I}"

    def test_herd_immunity_threshold_formula(self):
        """H = 1 - 1/R₀ must be correct."""
        model = SEIRDModel(N=10_000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.0, nu=0.0)
        expected_H = 1 - 1 / (0.30 / 0.10)
        assert abs(model.herd_immunity_threshold - expected_H) < 1e-10


# ---------------------------------------------------------------------------
# Test 3: Boundary conditions
# ---------------------------------------------------------------------------
class TestBoundaryConditions:
    def test_small_population(self):
        """Should run without error on N=1000, I0=1."""
        model = SEIRDModel(N=1000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.01, nu=0.0, I0=1)
        df = model.run(days=100)
        assert len(df) == 101

    def test_large_population(self):
        """Should run without error on N=1,000,000."""
        model = SEIRDModel(N=1_000_000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.01, nu=0.0, I0=5)
        df = model.run(days=50)
        assert len(df) == 51

    def test_zero_deaths_when_mu_zero(self):
        """When μ=0, deaths should always be zero."""
        model = SEIRDModel(N=10_000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.0, nu=0.0, I0=10)
        df = model.run(days=100)
        assert df["D"].max() < 1e-6, "Deaths non-zero when μ=0"

    def test_vaccination_reduces_susceptibles(self):
        """Vaccination (ν > 0) should result in fewer susceptibles than without."""
        params_no_vax = dict(N=10_000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.0, nu=0.0, I0=1)
        params_vax    = dict(N=10_000, beta=0.30, sigma=0.20, gamma=0.10, mu=0.0, nu=0.005, I0=1)
        df_no_vax = SEIRDModel(**params_no_vax).run(days=50)
        df_vax    = SEIRDModel(**params_vax).run(days=50)
        assert df_vax["S"].iloc[-1] < df_no_vax["S"].iloc[-1]


# ---------------------------------------------------------------------------
# Test 4: Intervention effects
# ---------------------------------------------------------------------------
class TestInterventions:
    def test_lockdown_reduces_peak(self):
        """A strict lockdown must reduce peak infected compared to no intervention."""
        model_base = SEIRDModel(**BASE)
        model_lock = SEIRDModel(**BASE)
        interv = Intervention("Strict lockdown", start_day=20, beta_reduction=0.60)

        df_base = model_base.run(days=300)
        df_lock = model_lock.run(days=300, intervention=interv)

        peak_base = df_base["I"].max()
        peak_lock = df_lock["I"].max()
        assert peak_lock < peak_base, (
            f"Lockdown did not reduce peak: baseline={peak_base:.0f}, lockdown={peak_lock:.0f}"
        )

    def test_early_lockdown_better_than_late(self):
        """Early intervention (day 15) should beat late intervention (day 45)."""
        early = Intervention("Early", start_day=15, beta_reduction=0.60)
        late  = Intervention("Late",  start_day=45, beta_reduction=0.60)
        df_early = SEIRDModel(**BASE).run(days=300, intervention=early)
        df_late  = SEIRDModel(**BASE).run(days=300, intervention=late)
        assert df_early["I"].max() < df_late["I"].max()


# ---------------------------------------------------------------------------
# Test 5: Summary statistics
# ---------------------------------------------------------------------------
class TestSummaryStatistics:
    def test_summary_keys_present(self):
        model = SEIRDModel(**BASE)
        df = model.run(days=200)
        summary = model.compute_summary(df)
        required_keys = ["R0", "peak_infected", "peak_day", "total_deaths",
                         "total_affected_pct", "herd_immunity_threshold_pct"]
        for k in required_keys:
            assert k in summary, f"Missing key: {k}"

    def test_peak_day_in_range(self):
        model = SEIRDModel(**BASE)
        df = model.run(days=200)
        summary = model.compute_summary(df)
        assert 0 <= summary["peak_day"] <= 200

    def test_total_affected_pct_is_percent(self):
        model = SEIRDModel(**BASE)
        df = model.run(days=365)
        summary = model.compute_summary(df)
        assert 0 <= summary["total_affected_pct"] <= 100


# ---------------------------------------------------------------------------
# Test 6: Sensitivity analysis
# ---------------------------------------------------------------------------
class TestSensitivityAnalysis:
    def test_higher_beta_means_higher_peak(self):
        """Increasing β should (generally) increase peak infected %."""
        df = sensitivity_analysis(BASE, param_name="beta",
                                  values=[0.10, 0.20, 0.30, 0.40, 0.50], days=200)
        peaks = df["peak_infected_pct"].tolist()
        # Should be monotonically increasing (allow tiny floating point noise)
        for i in range(1, len(peaks)):
            assert peaks[i] >= peaks[i-1] - 0.5, (
                f"Peak not increasing with β: {peaks}"
            )
