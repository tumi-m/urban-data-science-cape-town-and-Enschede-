"""Forecasting population to 2050, and being honest about what that means.

The central point this module is built to make visible is that on a series
this short and this smooth, **the choice of model matters more than the data**.
Seventy-five annual observations cannot distinguish between a city heading for
175,000 and one heading for 158,000; the model's functional form decides that,
and the functional form is an assumption, not a finding.

So the registry deliberately includes families that disagree with each other,
and every one of them reports whether it can extrapolate at all. Tree ensembles
cannot: a random forest predicts by averaging training targets, so beyond the
last observed year it emits a horizontal line for ever. That is not a bug to be
hidden behind a smooth-looking chart — it is the single most useful thing a
newcomer to forecasting can be shown, so the app shows it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, DotProduct, WhiteKernel
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


# ---------------------------------------------------------------------
# Parameter specification
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Param:
    key: str
    label: str
    kind: str  # "int" | "float" | "choice"
    default: Any
    low: Any = None
    high: Any = None
    step: Any = None
    options: tuple = ()
    help: str = ""


@dataclass
class ModelSpec:
    key: str
    label: str
    family: str
    params: list[Param]
    build: Callable[..., Any]
    extrapolates: bool
    uncertainty: bool
    blurb: str
    caution: str = ""


# ---------------------------------------------------------------------
# Mechanistic curves
# ---------------------------------------------------------------------
#
# These are not machine learning and are not pretending to be. They are in the
# registry because they are the right shape for the problem: settlement growth
# under a hard land constraint is a saturating process, and a model that cannot
# saturate will be wrong in the direction that matters. Putting them beside the
# learned models is the comparison the section exists to make.

def _logistic(t, capacity, rate, midpoint):
    return capacity / (1 + np.exp(-rate * (t - midpoint)))


def _gompertz(t, capacity, rate, midpoint):
    return capacity * np.exp(-np.exp(-rate * (t - midpoint)))


class _CurveModel:
    """Wraps a three-parameter growth curve in the estimator interface."""

    def __init__(self, fn, capacity_hint: float = 200_000, rate: float = 0.05):
        self.fn = fn
        self.capacity_hint = capacity_hint
        self.rate = rate
        self.popt_ = None
        self._t0 = 0.0

    def fit(self, X, y):
        t = np.asarray(X).ravel().astype(float)
        self._t0 = t.min()
        t = t - self._t0
        y = np.asarray(y, dtype=float)
        p0 = [self.capacity_hint, self.rate, float(np.median(t))]
        bounds = ([y.max() * 1.001, 1e-4, -200.0], [y.max() * 6, 1.0, 400.0])
        try:
            self.popt_, _ = curve_fit(self.fn, t, y, p0=p0, bounds=bounds, maxfev=40_000)
        except Exception:
            # A curve that will not converge should fall back to something
            # visibly wrong rather than silently returning the initial guess.
            self.popt_ = np.array([y.max() * 1.2, 0.03, float(np.median(t))])
        return self

    def predict(self, X):
        t = np.asarray(X).ravel().astype(float) - self._t0
        return self.fn(t, *self.popt_)

    @property
    def capacity(self) -> float:
        return float(self.popt_[0]) if self.popt_ is not None else float("nan")


class _GPWrapper:
    """Gaussian process on centred years, carrying its own uncertainty.

    The kernel is a linear term plus an RBF: the linear term lets it hold a
    trend beyond the data instead of reverting to the mean, which is what a
    pure RBF does and which makes a pure RBF useless for extrapolation.
    """

    def __init__(self, length_scale: float = 20.0, noise: float = 1.0):
        kernel = (
            ConstantKernel(1.0) * DotProduct(sigma_0=1.0)
            + ConstantKernel(1.0) * RBF(length_scale=length_scale)
            + WhiteKernel(noise_level=max(noise, 1e-3))
        )
        self.gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, alpha=1e-6)
        self._mu = 0.0
        self._sd = 1.0
        self._ymu = 0.0
        self._ysd = 1.0

    def fit(self, X, y):
        t = np.asarray(X, dtype=float).reshape(-1, 1)
        y = np.asarray(y, dtype=float)
        self._mu, self._sd = t.mean(), t.std() or 1.0
        self._ymu, self._ysd = y.mean(), y.std() or 1.0
        self.gp.fit((t - self._mu) / self._sd, (y - self._ymu) / self._ysd)
        return self

    def predict(self, X, return_std: bool = False):
        t = np.asarray(X, dtype=float).reshape(-1, 1)
        out = self.gp.predict((t - self._mu) / self._sd, return_std=return_std)
        if return_std:
            mean, std = out
            return mean * self._ysd + self._ymu, std * self._ysd
        return out * self._ysd + self._ymu


# ---------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------

MODELS: dict[str, ModelSpec] = {
    "linear": ModelSpec(
        key="linear", label="Linear trend", family="Regression",
        params=[],
        build=lambda **_: LinearRegression(),
        extrapolates=True, uncertainty=False,
        blurb="A straight line through the whole series. The honest baseline every other model "
              "has to beat, and on a plateauing city it is often hard to beat.",
        caution="Assumes the last seventy years and the next twenty-five are one process.",
    ),
    "poly": ModelSpec(
        key="poly", label="Polynomial ridge", family="Regression",
        params=[
            Param("degree", "Polynomial degree", "int", 2, 1, 5, 1,
                  help="Curvature the model may use. Past 3 it starts fitting the wobble and "
                       "the extrapolation swings violently."),
            Param("alpha", "Ridge penalty (α)", "float", 1.0, 0.0, 100.0, 0.5,
                  help="Shrinks coefficients toward zero. Higher is flatter and safer."),
        ],
        build=lambda degree=2, alpha=1.0: make_pipeline(
            PolynomialFeatures(degree=int(degree)), StandardScaler(),
            Ridge(alpha=float(alpha))),
        extrapolates=True, uncertainty=False,
        blurb="A curve rather than a line, penalised so it does not chase noise. Degree is the "
              "single most consequential control in this whole section.",
        caution="Polynomials diverge outside the fitted range. Degree 4 or 5 will produce a "
                "2050 figure you should not repeat in public.",
    ),
    "rf": ModelSpec(
        key="rf", label="Random forest", family="Tree ensemble",
        params=[
            Param("n_estimators", "Trees", "int", 300, 50, 800, 50),
            Param("max_depth", "Max depth", "int", 6, 2, 20, 1),
        ],
        build=lambda n_estimators=300, max_depth=6: RandomForestRegressor(
            n_estimators=int(n_estimators), max_depth=int(max_depth), random_state=0),
        extrapolates=False, uncertainty=True,
        blurb="Averages many decision trees. Excellent at interpolating structure, and "
              "structurally incapable of leaving the range of its training targets.",
        caution="Cannot extrapolate. Every forecast year beyond the data is the same number — "
                "the flat line on the chart is the model working exactly as designed.",
    ),
    "gbm": ModelSpec(
        key="gbm", label="Gradient boosting", family="Tree ensemble",
        params=[
            Param("n_estimators", "Boosting rounds", "int", 300, 50, 800, 50),
            Param("learning_rate", "Learning rate", "float", 0.05, 0.01, 0.5, 0.01),
            Param("max_depth", "Max depth", "int", 3, 1, 8, 1),
        ],
        build=lambda n_estimators=300, learning_rate=0.05, max_depth=3: GradientBoostingRegressor(
            n_estimators=int(n_estimators), learning_rate=float(learning_rate),
            max_depth=int(max_depth), random_state=0),
        extrapolates=False, uncertainty=False,
        blurb="Fits trees to the previous round's residuals. The best in-sample fit in the "
              "registry, and the same flat-line failure beyond the data.",
        caution="Cannot extrapolate. A near-perfect backtest score here is a warning, not a "
                "recommendation.",
    ),
    "gp": ModelSpec(
        key="gp", label="Gaussian process", family="Probabilistic",
        params=[
            Param("length_scale", "RBF length scale (years)", "float", 20.0, 2.0, 60.0, 1.0,
                  help="How far the model expects the series to stay correlated with itself."),
            Param("noise", "Noise level", "float", 1.0, 0.01, 10.0, 0.05),
        ],
        build=lambda length_scale=20.0, noise=1.0: _GPWrapper(float(length_scale), float(noise)),
        extrapolates=True, uncertainty=True,
        blurb="A distribution over functions rather than a single curve, so it returns a band "
              "as well as a line. The only model here whose uncertainty widens honestly the "
              "further out it goes.",
        caution="The band is the model's uncertainty given its kernel — not uncertainty about "
                "whether the kernel was the right choice.",
    ),
    "logistic": ModelSpec(
        key="logistic", label="Logistic (Verhulst) curve", family="Mechanistic",
        params=[
            Param("capacity_hint", "Capacity starting guess", "int", 200_000, 165_000, 400_000,
                  5_000, help="Initial guess for the saturation level; the fit moves it."),
            Param("rate", "Growth rate starting guess", "float", 0.05, 0.005, 0.3, 0.005),
        ],
        build=lambda capacity_hint=200_000, rate=0.05: _CurveModel(
            _logistic, float(capacity_hint), float(rate)),
        extrapolates=True, uncertainty=False,
        blurb="Growth that slows as it approaches a ceiling. The right shape for a city whose "
              "land supply is fixed, and it estimates the ceiling rather than assuming it.",
        caution="Symmetric around its inflection, which real settlement growth rarely is.",
    ),
    "gompertz": ModelSpec(
        key="gompertz", label="Gompertz curve", family="Mechanistic",
        params=[
            Param("capacity_hint", "Capacity starting guess", "int", 200_000, 165_000, 400_000,
                  5_000),
            Param("rate", "Growth rate starting guess", "float", 0.05, 0.005, 0.3, 0.005),
        ],
        build=lambda capacity_hint=200_000, rate=0.05: _CurveModel(
            _gompertz, float(capacity_hint), float(rate)),
        extrapolates=True, uncertainty=False,
        blurb="A saturating curve that rises fast and decelerates slowly — asymmetric, which "
              "fits a city that grew quickly then stalled better than a logistic does.",
        caution="Sensitive to the starting guess; move the capacity slider and watch 2050 move.",
    ),
}


# ---------------------------------------------------------------------
# Fitting and evaluation
# ---------------------------------------------------------------------

@dataclass
class Fit:
    spec: ModelSpec
    model: Any
    history: pd.DataFrame
    forecast: pd.DataFrame
    metrics: dict
    backtest: pd.DataFrame
    residuals: pd.DataFrame
    capacity: float | None = None
    warnings: list[str] = field(default_factory=list)


def _predict(model, years: np.ndarray, want_std: bool):
    X = np.asarray(years, dtype=float).reshape(-1, 1)
    if want_std and hasattr(model, "predict"):
        try:
            return model.predict(X, return_std=True)
        except TypeError:
            pass
    return np.asarray(model.predict(X)), None


def fit_and_forecast(
    history: pd.DataFrame,
    spec: ModelSpec,
    params: dict,
    horizon_year: int = 2050,
    holdout_years: int = 15,
) -> Fit:
    """Fit, backtest on a held-out tail, and project to the horizon.

    The backtest is a single contiguous holdout at the end of the series rather
    than a random split, because a random split on a time series lets the model
    see the future while predicting the past and returns a score that means
    nothing. Holding out the tail asks the only question worth asking: standing
    in year T, how wrong would this model have been about the years that
    followed?
    """
    hist = history.sort_values("year").reset_index(drop=True)
    years = hist["year"].to_numpy(dtype=float)
    values = hist["population"].to_numpy(dtype=float)

    # --- backtest on the tail -----------------------------------------
    holdout_years = int(min(max(holdout_years, 3), len(hist) // 3))
    split = len(hist) - holdout_years
    bt_model = spec.build(**params)
    bt_model.fit(years[:split].reshape(-1, 1), values[:split])
    bt_pred, _ = _predict(bt_model, years[split:], False)

    metrics = {
        "MAE": float(mean_absolute_error(values[split:], bt_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(values[split:], bt_pred))),
        "MAPE %": float(np.mean(np.abs((values[split:] - bt_pred) / values[split:])) * 100),
        "R²": float(r2_score(values[split:], bt_pred)),
        "Holdout years": holdout_years,
        "Trained on": f"{int(years[0])}–{int(years[split - 1])}",
        "Tested on": f"{int(years[split])}–{int(years[-1])}",
    }
    backtest = pd.DataFrame({
        "year": years[split:].astype(int),
        "actual": values[split:],
        "predicted": bt_pred,
    })

    # --- refit on everything, then project ----------------------------
    model = spec.build(**params)
    model.fit(years.reshape(-1, 1), values)

    in_sample, _ = _predict(model, years, False)
    residuals = pd.DataFrame({
        "year": years.astype(int),
        "residual": values - np.asarray(in_sample),
    })

    future = np.arange(years[-1] + 1, horizon_year + 1, dtype=float)
    mean, std = _predict(model, future, spec.uncertainty)
    mean = np.asarray(mean, dtype=float)

    forecast = pd.DataFrame({"year": future.astype(int), "population": mean})
    if std is not None:
        forecast["lower"] = mean - 1.96 * np.asarray(std)
        forecast["upper"] = mean + 1.96 * np.asarray(std)

    warnings: list[str] = []
    if not spec.extrapolates:
        flat = float(np.ptp(mean))
        warnings.append(
            f"This family cannot extrapolate. Its projection varies by {flat:,.0f} people "
            f"across {len(future)} years — effectively a horizontal line, which is the model "
            f"reporting that it has nothing to say beyond {int(years[-1])}."
        )
    if spec.key == "poly" and int(params.get("degree", 2)) >= 4:
        warnings.append(
            "At degree 4 or above the extrapolation is dominated by the highest-order term. "
            "The 2050 figure is an artefact of the basis, not a finding about Enschede."
        )
    change = mean[-1] - values[-1]
    if abs(change) > 0.35 * values[-1]:
        warnings.append(
            f"The projection implies a {change / values[-1] * 100:+.0f}% change by "
            f"{horizon_year}. No Dutch city of this size has moved that far in a comparable "
            "period; treat it as a property of the model."
        )

    capacity = getattr(model, "capacity", None)
    return Fit(spec, model, hist, forecast, metrics, backtest, residuals,
               capacity if isinstance(capacity, float) else None, warnings)


def compare_all(history: pd.DataFrame, horizon_year: int = 2050,
                holdout_years: int = 15) -> pd.DataFrame:
    """Every model at its defaults, side by side.

    This table is the section's real argument. The spread across the 2050 column
    is much wider than any single model's confidence band, which is the thing a
    single forecast with a tidy interval will never tell you.
    """
    rows = []
    for spec in MODELS.values():
        defaults = {p.key: p.default for p in spec.params}
        try:
            fit = fit_and_forecast(history, spec, defaults, horizon_year, holdout_years)
        except Exception as exc:  # a model that fails should say so, not vanish
            rows.append({"Model": spec.label, "Family": spec.family,
                         "2050": float("nan"), "MAE": float("nan"),
                         "MAPE %": float("nan"), "Extrapolates": spec.extrapolates,
                         "Note": f"failed: {type(exc).__name__}"})
            continue
        rows.append({
            "Model": spec.label,
            "Family": spec.family,
            "2050": float(fit.forecast["population"].iloc[-1]),
            "MAE": fit.metrics["MAE"],
            "MAPE %": fit.metrics["MAPE %"],
            "Extrapolates": spec.extrapolates,
            "Note": fit.warnings[0][:80] + "…" if fit.warnings else "",
        })
    return pd.DataFrame(rows)
