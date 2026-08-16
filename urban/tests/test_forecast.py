"""Tests for the forecast registry.

The module's central claim is that model choice dominates data on short smooth
series, and that every model must report whether it can extrapolate. These
tests pin that contract down: registry invariants, curve behaviour beyond the
data, the flat-line failure of tree ensembles, backtest honesty (contiguous
tail holdout, never a random split), calibrated conformal bands, and the
ensemble's inverse-MAE weighting.
"""

import numpy as np
import pandas as pd
import pytest

from urban.forecast import (
    MODELS,
    Fit,
    ModelSpec,
    Param,
    _CurveModel,
    _GPWrapper,
    _gompertz,
    _logistic,
    add_conformal,
    compare_all,
    conformal_band,
    ensemble_forecast,
    fit_and_forecast,
)


CAP = 180_000.0
RATE = 0.05
MID = 1990.0


def make_history(n: int = 75, noise: float = 250.0, seed: int = 7) -> pd.DataFrame:
    """A synthetic city that saturates, Enschede-shaped, with mild noise."""
    rng = np.random.default_rng(seed)
    years = np.arange(1950, 1950 + n)
    pop = _logistic(years.astype(float), CAP, RATE, MID) + rng.normal(0.0, noise, n)
    return pd.DataFrame({"year": years, "population": pop})


@pytest.fixture
def history() -> pd.DataFrame:
    return make_history()


def defaults(spec: ModelSpec) -> dict:
    return {p.key: p.default for p in spec.params}


# ---------------------------------------------------------------------
# Mechanistic curves
# ---------------------------------------------------------------------

def test_logistic_saturates_at_capacity():
    t = np.array([1950.0, 2000.0, 2100.0, 2300.0])
    y = _logistic(t, CAP, RATE, MID)
    assert y[0] < y[1] < y[2] < y[3]  # monotonically rising
    assert y[3] == pytest.approx(CAP, rel=1e-3)  # and it converges to capacity


def test_gompertz_saturates_at_capacity():
    t = np.array([1950.0, 2000.0, 2100.0, 2300.0])
    y = _gompertz(t, CAP, RATE, MID)
    assert np.all(np.diff(y) > 0)
    assert y[3] == pytest.approx(CAP, rel=1e-3)


def test_curve_model_recovers_capacity(history):
    model = _CurveModel(_logistic, capacity_hint=200_000, rate=0.05)
    X = history["year"].to_numpy(dtype=float).reshape(-1, 1)
    model.fit(X, history["population"].to_numpy())
    # Bounds keep the fit within [y.max()*1.001, y.max()*6].
    assert model.capacity > history["population"].max() * 0.99
    assert model.capacity < history["population"].max() * 6.01


def test_curve_model_predicts_beyond_data(history):
    model = _CurveModel(_logistic, capacity_hint=200_000, rate=0.05)
    X = history["year"].to_numpy(dtype=float).reshape(-1, 1)
    model.fit(X, history["population"].to_numpy())
    far = np.array([2050.0, 2100.0, 2200.0])
    pred = model.predict(far)
    # Monotone rise towards, but never above, the fitted capacity.
    assert np.all(np.diff(pred) >= -1e-6)
    assert np.all(pred <= model.capacity * (1 + 1e-6))


def test_curve_model_falls_back_when_fit_fails():
    def broken(t, capacity, rate, midpoint):
        raise RuntimeError("never converges")

    years = np.arange(1950.0, 2000.0)
    values = _logistic(years, CAP, RATE, MID)
    model = _CurveModel(broken)
    model.fit(years.reshape(-1, 1), values)  # must not raise
    # Fallback capacity is visibly wrong (1.2x the max), not the initial guess,
    # and the fallback parameters themselves are finite.
    assert model.capacity == pytest.approx(values.max() * 1.2)
    assert np.isfinite(model.popt_).all()


# ---------------------------------------------------------------------
# Gaussian process wrapper
# ---------------------------------------------------------------------

def test_gp_wrapper_carries_uncertainty(history):
    X = history["year"].to_numpy(dtype=float).reshape(-1, 1)
    y = history["population"].to_numpy(dtype=float)
    gp = _GPWrapper(length_scale=20.0, noise=1.0).fit(X, y)
    inside, std_in = gp.predict(X[:5], return_std=True)
    outside, std_out = gp.predict(np.array([[2060.0], [2080.0]]), return_std=True)
    assert np.all(std_out > 0)
    # Uncertainty must widen honestly beyond the data — that is the point of
    # putting a DotProduct term in the kernel.
    assert std_out.mean() > std_in.mean()
    # Predictions on training years should be close to the observations.
    assert np.abs(inside - y[:5]).mean() < 5_000


# ---------------------------------------------------------------------
# Registry invariants
# ---------------------------------------------------------------------

def test_registry_has_both_extrapolating_and_not():
    extrapolates = {s.extrapolates for s in MODELS.values()}
    assert extrapolates == {True, False}, "the comparison needs families that disagree"


def test_registry_keys_are_unique():
    keys = list(MODELS)
    assert len(keys) == len(set(keys))
    for key, spec in MODELS.items():
        assert spec.key == key


def test_param_defaults_within_bounds():
    for spec in MODELS.values():
        for p in spec.params:
            if p.kind in ("int", "float") and p.low is not None:
                assert p.low <= p.default <= p.high, (spec.key, p.key)


def test_every_model_has_blurb_and_build():
    for spec in MODELS.values():
        assert callable(spec.build)
        assert len(spec.blurb) > 20
        # build() must accept its own defaults
        model = spec.build(**defaults(spec))
        assert hasattr(model, "fit") and hasattr(model, "predict")


# ---------------------------------------------------------------------
# fit_and_forecast
# ---------------------------------------------------------------------

def test_fit_and_forecast_linear(history):
    fit = fit_and_forecast(history, MODELS["linear"], {}, horizon_year=2050)
    last = int(history["year"].max())
    assert isinstance(fit, Fit)
    assert fit.forecast["year"].tolist() == list(range(last + 1, 2051))
    assert np.isfinite(fit.forecast["population"]).all()


def test_backtest_is_contiguous_tail(history):
    fit = fit_and_forecast(history, MODELS["linear"], {}, 2050, holdout_years=15)
    n = len(history)
    assert fit.metrics["Holdout years"] == 15
    expected_first = history["year"].iloc[n - 15]
    assert fit.backtest["year"].iloc[0] == expected_first
    # No gap and no overlap between train and test.
    assert fit.metrics["Tested on"].startswith(str(expected_first))


def test_holdout_is_clamped_short_series():
    short = make_history(n=12)
    fit = fit_and_forecast(short, MODELS["linear"], {}, 2050, holdout_years=15)
    # len//3 = 4, so the request for 15 is clamped to 4.
    assert fit.metrics["Holdout years"] == 4


def test_tree_ensemble_flat_line_is_flagged(history):
    fit = fit_and_forecast(history, MODELS["rf"], defaults(MODELS["rf"]))
    assert MODELS["rf"].extrapolates is False
    assert fit.warnings, "a non-extrapolating model must say so"
    assert any("cannot extrapolate" in w for w in fit.warnings)
    # And the projection itself is a horizontal line.
    assert np.ptp(fit.forecast["population"].to_numpy()) < 1e-6


def test_tree_ensemble_backtest_is_flat_too(history):
    """The tail holdout is *past* the tree's training range, so even the
    backtest is extrapolation: a flat line whose MAE reflects exactly that
    failure — the module's own caution about near-perfect in-sample scores."""
    fit = fit_and_forecast(history, MODELS["rf"], defaults(MODELS["rf"]))
    assert np.ptp(fit.backtest["predicted"].to_numpy()) < 1e-6
    linear = fit_and_forecast(history, MODELS["linear"], {})
    assert fit.metrics["MAE"] > linear.metrics["MAE"]


def test_gp_fit_has_native_band(history):
    fit = fit_and_forecast(history, MODELS["gp"], defaults(MODELS["gp"]))
    assert {"lower", "upper"} <= set(fit.forecast.columns)
    assert np.all(fit.forecast["upper"] > fit.forecast["lower"])


def test_curve_fits_report_capacity(history):
    fit = fit_and_forecast(history, MODELS["logistic"], defaults(MODELS["logistic"]))
    assert fit.capacity is not None and np.isfinite(fit.capacity)
    assert fit.capacity > history["population"].max()


def test_high_degree_poly_warns(history):
    params = defaults(MODELS["poly"]) | {"degree": 5}
    fit = fit_and_forecast(history, MODELS["poly"], params)
    assert any("degree 4" in w for w in fit.warnings)


def test_history_is_sorted_not_mutated():
    scrambled = make_history().iloc[::-1].reset_index(drop=True)
    snapshot = scrambled.copy()
    fit = fit_and_forecast(scrambled, MODELS["linear"], {})
    assert fit.history["year"].is_monotonic_increasing
    pd.testing.assert_frame_equal(scrambled, snapshot)


def test_metrics_are_finite_for_defaults(history):
    for key, spec in MODELS.items():
        fit = fit_and_forecast(history, spec, defaults(spec))
        for m in ("MAE", "RMSE", "MAPE %", "R²"):
            assert np.isfinite(fit.metrics[m]), (key, m)
        # Residuals align with the history years.
        assert len(fit.residuals) == len(history)
        assert np.isfinite(fit.residuals["residual"]).all()


# ---------------------------------------------------------------------
# compare_all
# ---------------------------------------------------------------------

def test_compare_all_covers_registry(history):
    table = compare_all(history)
    assert len(table) == len(MODELS)
    assert set(table["Model"]) == {s.label for s in MODELS.values()}
    assert set(["Model", "Family", "2050", "MAE", "MAPE %", "Extrapolates"]) <= set(table.columns)


def test_compare_all_failures_are_reported_not_hidden():
    broken = pd.DataFrame({
        "year": [2000, 2001, 2002],
        "population": [np.nan, 100_000.0, np.nan],
    })
    table = compare_all(broken)
    assert len(table) == len(MODELS)
    # Every failing row says which exception, instead of vanishing.
    failed = table[table["Note"].str.startswith("failed:", na=False)]
    assert (failed["2050"].isna()).all()
    assert failed["Note"].str.contains("failed: ").all()


def test_compare_all_spread_exceeds_single_band(history):
    """The section's argument: model disagreement dwarfs any one interval."""
    table = compare_all(history).dropna(subset=["2050"])
    fit = fit_and_forecast(history, MODELS["logistic"], defaults(MODELS["logistic"]))
    lo, hi = conformal_band(fit, alpha=0.10)
    single_half = float((hi[-1] - lo[-1]) / 2)
    spread = float(table["2050"].max() - table["2050"].min())
    assert spread > single_half


# ---------------------------------------------------------------------
# Conformal bands
# ---------------------------------------------------------------------

def test_conformal_band_brackets_mean_and_widens(history):
    fit = fit_and_forecast(history, MODELS["linear"], {})
    lo, hi = conformal_band(fit, alpha=0.10)
    mean = fit.forecast["population"].to_numpy()
    assert np.all(lo <= mean + 1e-9) and np.all(hi >= mean - 1e-9)
    # The square-root growth factor must widen the band with steps ahead.
    half = (hi - lo) / 2
    assert np.all(np.diff(half) > 0)
    # And it never drops below zero.
    assert np.all(lo >= 0)


def test_conformal_band_loosens_with_alpha(history):
    fit = fit_and_forecast(history, MODELS["linear"], {})
    strict = conformal_band(fit, alpha=0.01)
    loose = conformal_band(fit, alpha=0.50)
    assert np.all(strict[1] - strict[0] >= loose[1] - loose[0])


def test_conformal_band_matches_backtest_errors(history):
    fit = fit_and_forecast(history, MODELS["linear"], {})
    lo, hi = conformal_band(fit, alpha=0.10)
    errors = np.abs(fit.backtest["actual"] - fit.backtest["predicted"]).to_numpy()
    n = len(errors)
    # Finite-sample conformal level, then a sqrt widening with steps ahead.
    level = min(1.0, np.ceil((n + 1) * 0.90) / n)
    q = np.quantile(errors, level, method="higher")
    steps = np.maximum(
        fit.forecast["year"].to_numpy(dtype=float) - float(fit.history["year"].iloc[-1]), 0.0)
    expected_half = q * np.sqrt(1.0 + 0.6 * steps / n)
    np.testing.assert_allclose(hi - lo, 2 * expected_half, rtol=1e-9)


def test_add_conformal_attaches_columns(history):
    fit = fit_and_forecast(history, MODELS["linear"], {})
    out = add_conformal(fit, alpha=0.10)
    assert out is fit  # in place, returns the same Fit
    assert {"conf_lower", "conf_upper"} <= set(fit.forecast.columns)


# ---------------------------------------------------------------------
# Ensemble
# ---------------------------------------------------------------------

def test_ensemble_weights_and_shape(history):
    result = ensemble_forecast(history, horizon_year=2050)
    last = int(history["year"].max())
    assert result["years"].tolist() == list(range(last + 1, 2051))
    assert len(result["mean"]) == len(result["years"])
    assert len(result["members"]) > 0
    weights = [m["weight"] for m in result["members"]]
    assert sum(weights) == pytest.approx(1.0)
    # Only families that can extrapolate get to vote.
    member_labels = {m["model"] for m in result["members"]}
    non_extrapolating = {s.label for s in MODELS.values() if not s.extrapolates}
    assert not (member_labels & non_extrapolating)


def test_ensemble_band_brackets_mean(history):
    result = ensemble_forecast(history, horizon_year=2050)
    assert np.all(result["lower"] <= result["mean"] + 1e-9)
    assert np.all(result["upper"] >= result["mean"] - 1e-9)
    assert np.all(result["lower"] >= 0)


def test_ensemble_mean_is_weighted_convex_combination(history):
    result = ensemble_forecast(history, horizon_year=2050)
    fits = []
    for spec in MODELS.values():
        if not spec.extrapolates:
            continue
        try:
            fit = fit_and_forecast(history, spec, defaults(spec), 2050, 15)
        except Exception:
            continue
        if np.isfinite(fit.metrics["MAE"]):
            fits.append(fit)
    stacked = np.vstack([f.forecast["population"].to_numpy(dtype=float) for f in fits])
    weights = np.array([1.0 / max(f.metrics["MAE"], 1.0) for f in fits])
    weights /= weights.sum()
    expected = (weights[:, None] * stacked).sum(axis=0)
    np.testing.assert_allclose(result["mean"], expected, rtol=1e-6)


def test_ensemble_lower_mae_gets_higher_weight(history):
    result = ensemble_forecast(history, horizon_year=2050)
    maes = np.array([m["mae"] for m in result["members"]])
    weights = np.array([m["weight"] for m in result["members"]])
    order = np.argsort(maes)
    # The best (lowest-MAE) member must outweigh the worst.
    assert weights[order[0]] > weights[order[-1]]





