"""Scaling the behavioural model, after Light Society.

Adapted from Guan et al., "Modeling Earth-Scale Human-Like Societies with One
Billion Agents" (arXiv:2506.12078). Two ideas from that paper are taken up here
because they solve problems this project actually has.

**1. Social processes as structured state transitions.**
Light Society formalises a simulation as agent states and an environment state,
moved forward by a set of named operations rather than by one loop that does
everything. The behaviour module already had the ingredients but not the shape:
its market clearing, location choice and mode choice were tangled in a single
function, so you could not swap one out, time one, or say which step produced a
result. Here each step is an `Operation` with a name, and a run is a list of
them applied in order.

**2. A mixture-of-models engine with distilled surrogates.**
Their central efficiency result is that you do not need to run the expensive
high-fidelity agent model for every agent. Run it for a sample, distil a cheap
surrogate from those outputs, and use the surrogate for the rest — keeping the
expensive model where fidelity matters. That is what lets them reach a billion
agents, and it is exactly the constraint here: the full model is a logit over
every household against every location inside a market-clearing loop, which is
fine at three thousand households and hopeless at three million.

**What is not taken up, and must not be implied.** Light Society's high-fidelity
operator is a large language model, and its agents are people with beliefs and
opinions doing Trust Games and diffusing opinions. There is no LLM anywhere in
this module. The high-fidelity operator here is a random-utility discrete-choice
model — cheaper, far narrower, and answering a different question. What has been
borrowed is the *architecture*: structured operations, and distil-then-scale.
Calling this an LLM agent society would be false.

Their agents are also grounded in real demographic profiles from the World
Values Survey. Ours are grounded in a synthetic income distribution, which is
the weakest part of this and is labelled as such wherever it is used.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from . import behaviour as bh


# ---------------------------------------------------------------------
# State
# ---------------------------------------------------------------------

@dataclass
class AgentState:
    """What every household is and currently has decided.

    Columns rather than objects: a million dataclass instances is a million
    Python objects, and the whole point of this module is that the population
    is allowed to get large.
    """

    frame: pd.DataFrame

    def __len__(self) -> int:
        return len(self.frame)


@dataclass
class EnvironmentState:
    """What everyone shares: the places, their rents, and the current policy."""

    rings: pd.DataFrame
    policy: bh.Policy
    step: int = 0
    log: list[str] = field(default_factory=list)


@dataclass
class Operation:
    """One named transition. The unit a run is assembled from."""

    name: str
    fn: Callable[[AgentState, EnvironmentState], tuple[AgentState, EnvironmentState]]
    description: str = ""

    def __call__(self, agents: AgentState, env: EnvironmentState):
        started = time.perf_counter()
        agents, env = self.fn(agents, env)
        env.log.append(f"{self.name}: {(time.perf_counter() - started) * 1000:.1f} ms")
        return agents, env


# ---------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------

def op_perceive(agents: AgentState, env: EnvironmentState):
    """Each household works out what every location would cost it.

    Rent plus the annual generalised cost of commuting from there — the logsum
    of the mode choice, so a location gets credit for having good options and
    not only for the one option a household would pick.

    Two things make this cheap, and both matter once the population is large.
    It depends only on distance and the household's value of time, so it is
    computed for the handful of distinct values of time and then broadcast
    rather than evaluated per household. And it does not depend on rents, so it
    survives the clearing loop instead of being rebuilt on every round.
    """
    if "commute_cost" in agents.frame.attrs:
        return agents, env

    dist = env.rings["km_to_centre"].to_numpy()
    vot = agents.frame["vot"].to_numpy()
    unique = np.unique(vot)
    by_vot = {
        v: np.array([bh._annual_commute_cost(d, float(v), env.policy) for d in dist])
        for v in unique
    }
    lookup = np.searchsorted(unique, vot)
    agents.frame.attrs["commute_cost"] = np.stack([by_vot[v] for v in unique])[lookup]
    return agents, env


def op_choose_location(agents: AgentState, env: EnvironmentState):
    """Logit over locations, given rents and what the household perceived."""
    rent = env.rings["rent"].to_numpy()
    dist = env.rings["km_to_centre"].to_numpy()
    budget = agents.frame["rent_budget"].to_numpy()[:, None]
    commute = agents.frame.attrs["commute_cost"]

    residual = budget - rent[None, :] - commute
    space = 0.18 * np.log1p(dist)[None, :]
    overspend = -3.0 * np.clip((rent[None, :] - budget) / budget, 0, None)
    u = residual / 10_000 + space + overspend

    p = bh._softmax(u)
    agents.frame.attrs["location_p"] = p
    agents.frame["ring"] = p.argmax(axis=1)
    agents.frame["expected_km"] = p @ dist
    return agents, env


def op_clear_market(agents: AgentState, env: EnvironmentState):
    """Rents move toward the level where demand matches what exists.

    One step, not a loop: the loop belongs to the run, so that a caller can see
    convergence happen rather than being handed the answer.
    """
    p = agents.frame.attrs["location_p"]
    demand = p.sum(axis=0)
    capacity = env.rings["capacity"].to_numpy()
    capacity = capacity / capacity.sum() * len(agents)

    gap = (demand - capacity) / np.maximum(capacity, 1)
    env.rings["rent"] = np.clip(
        env.rings["rent"].to_numpy() * (1 + 0.28 * gap), 1_500, 60_000)
    env.rings["households"] = demand
    env.rings["gap"] = gap
    env.step += 1
    return agents, env


def op_choose_mode(agents: AgentState, env: EnvironmentState):
    """Given where they ended up, how they get to work."""
    km = agents.frame["expected_km"].to_numpy()
    vot = agents.frame["vot"].to_numpy()
    shares = bh.mode_shares_array(km, vot, env.policy)
    for i, mode in enumerate(bh.MODES):
        agents.frame[f"p_{mode}"] = shares[:, i]
    agents.frame["car_km"] = (
        agents.frame["p_Car"] * km * bh.WORKING_DAYS * bh.TRIPS_PER_DAY)
    return agents, env


PIPELINE = [
    Operation("perceive", op_perceive,
              "Each household prices every location: rent plus the cost of getting to work."),
    Operation("choose_location", op_choose_location,
              "Logit over locations."),
    Operation("clear_market", op_clear_market,
              "Rents move toward the level where demand matches supply."),
    Operation("choose_mode", op_choose_mode,
              "Logit over travel modes, given where the household ended up."),
]


def run(policy: bh.Policy, n: int = 3000, rounds: int = 20,
        seed: int = 0, n_rings: int = 12) -> tuple[AgentState, EnvironmentState]:
    """Apply the operations until rents stop moving.

    `n_rings` is the number of distinct locations. It is a parameter rather than
    a constant because the cost of this model is households × locations, and the
    question of when a cheap approximation is worth having turns entirely on
    that product rather than on the population alone.
    """
    agents = AgentState(bh.households(n, seed))
    rings = bh.locations(n_rings).copy()
    rings["rent"] = 7_000.0
    env = EnvironmentState(rings, policy)

    for _ in range(rounds):
        for op in PIPELINE[:3]:
            agents, env = op(agents, env)
        if np.abs(env.rings["gap"]).max() < 0.012:
            break
    agents, env = PIPELINE[3](agents, env)
    return agents, env


# ---------------------------------------------------------------------
# The mixture-of-models engine
# ---------------------------------------------------------------------

SURROGATE_FEATURES = ["income", "vot", "rent_budget", "parking", "fuel", "ebike", "transit"]


def _feature_frame(agents: pd.DataFrame, policy: bh.Policy) -> pd.DataFrame:
    """Household attributes plus the policy, which is what the surrogate learns over.

    Putting the policy in the features is what makes one surrogate usable across
    scenarios rather than needing a fresh one per run.
    """
    return pd.DataFrame({
        "income": agents["income"].to_numpy(),
        "vot": agents["vot"].to_numpy(),
        "rent_budget": agents["rent_budget"].to_numpy(),
        "parking": policy.parking_charge_per_trip,
        "fuel": policy.fuel_cost_multiplier,
        "ebike": policy.ebike_subsidy,
        "transit": policy.transit_speed_multiplier,
    })


@dataclass
class Surrogate:
    """A distilled stand-in for the full model.

    Trained on what the expensive model produced for a sample of households
    across a spread of policies. Predicts the two outputs everything downstream
    needs — expected commute distance and car-kilometres — without the logit,
    the location matrix or the clearing loop.
    """

    km_model: HistGradientBoostingRegressor
    car_model: HistGradientBoostingRegressor
    fit_seconds: float
    train_rows: int
    scores: dict

    def predict(self, agents: pd.DataFrame, policy: bh.Policy) -> pd.DataFrame:
        X = _feature_frame(agents, policy)
        return pd.DataFrame({
            "expected_km": self.km_model.predict(X),
            "car_km": self.car_model.predict(X),
        })


def distil(sample_size: int = 2500, policies: list[bh.Policy] | None = None,
           seed: int = 0) -> Surrogate:
    """Run the full model on a sample, then learn to imitate it.

    This is the paper's move, in miniature: the expensive operator is used to
    generate training data rather than to serve every agent.
    """
    policies = policies or bh.SCENARIOS
    frames, km_y, car_y = [], [], []
    for i, pol in enumerate(policies):
        agents, _ = run(pol, n=sample_size, seed=seed + i)
        frames.append(_feature_frame(agents.frame, pol))
        km_y.append(agents.frame["expected_km"].to_numpy())
        car_y.append(agents.frame["car_km"].to_numpy())

    X = pd.concat(frames, ignore_index=True)
    y_km = np.concatenate(km_y)
    y_car = np.concatenate(car_y)

    started = time.perf_counter()
    km_model = HistGradientBoostingRegressor(max_iter=220, random_state=0).fit(X, y_km)
    car_model = HistGradientBoostingRegressor(max_iter=220, random_state=0).fit(X, y_car)
    elapsed = time.perf_counter() - started

    scores = {
        "km R²": float(r2_score(y_km, km_model.predict(X))),
        "car-km R²": float(r2_score(y_car, car_model.predict(X))),
        "car-km MAE": float(mean_absolute_error(y_car, car_model.predict(X))),
    }
    return Surrogate(km_model, car_model, elapsed, len(X), scores)


def policy_grid(n_random: int = 5, seed: int = 4) -> list[bh.Policy]:
    """A designed set of training policies, rather than the ones we happened to name.

    Six named scenarios sound like plenty until you notice they contain only two
    distinct parking charges. A gradient-boosted tree is constant between the
    values it was shown, so a surrogate distilled on those six answers every
    charge between €0 and €2.50 with the number it learned for €0.

    The obvious repair — draw all four levers uniformly at random — is worse,
    and instructively so. Draw an e-bike subsidy from €0–600 fourteen times and
    almost every training policy has a large one, so the surrogate never sees a
    city without a subsidy and puts car use far too low everywhere. Random is
    not the same as covering.

    What works is the dull classical answer: move each lever on its own across
    its range with the others at today's value, keep today's policy itself in
    the set, and add a few random combinations on top because levers interact.
    One factor at a time for the main effects, random draws for the rest.
    """
    grid = [bh.Policy("today")]

    for charge in np.linspace(0.5, 8.0, 6):
        grid.append(bh.Policy(f"parking {charge:.1f}",
                              parking_charge_per_trip=float(charge)))
    for fuel in (0.65, 0.85, 1.3, 1.7):
        grid.append(bh.Policy(f"fuel {fuel}", fuel_cost_multiplier=fuel))
    for sub in (150.0, 400.0, 650.0):
        grid.append(bh.Policy(f"ebike {sub:.0f}", ebike_subsidy=sub))
    for speed in (0.85, 1.2, 1.55):
        grid.append(bh.Policy(f"transit {speed}", transit_speed_multiplier=speed))

    # Interactions. Each lever keeps a real chance of sitting at today's value,
    # because policies in the world are sparse combinations rather than four
    # dials all turned at once.
    rng = np.random.default_rng(seed)
    for i in range(n_random):
        grid.append(bh.Policy(
            f"mix {i}",
            parking_charge_per_trip=float(rng.uniform(0, 8)) if rng.random() < 0.6 else 0.0,
            fuel_cost_multiplier=float(rng.uniform(0.6, 1.7)) if rng.random() < 0.6 else 1.0,
            ebike_subsidy=float(rng.uniform(0, 600)) if rng.random() < 0.6 else 0.0,
            transit_speed_multiplier=(
                float(rng.uniform(0.8, 1.6)) if rng.random() < 0.6 else 1.0),
        ))
    return grid


def holdout_agreement(surrogate: Surrogate, policy: bh.Policy,
                      n: int = 2000, seed: int = 99) -> dict:
    """Check the surrogate against the full model on a policy it was trained on.

    Agreement on held-out households is the claim that matters: if the surrogate
    only reproduces the sample it saw, it buys nothing.
    """
    agents, _ = run(policy, n=n, seed=seed)
    pred = surrogate.predict(agents.frame, policy)
    return {
        "Full-model car-km": float(agents.frame["car_km"].mean()),
        "Surrogate car-km": float(pred["car_km"].mean()),
        "R² on households": float(r2_score(agents.frame["car_km"], pred["car_km"])),
        "MAE, km per year": float(
            mean_absolute_error(agents.frame["car_km"], pred["car_km"])),
    }


CHARGE_SWEEP = (0.0, 0.75, 1.25, 2.0, 2.5, 3.25, 3.75, 5.0, 6.25, 7.5)


def scenario_agreement(narrow: Surrogate, wide: Surrogate,
                       n: int = 1000) -> pd.DataFrame:
    """Both surrogates against the full model, on each named scenario.

    Put beside the coverage sweep, this is the whole trade-off in two tables.
    The narrow surrogate was trained on exactly these six policies and
    reproduces them almost exactly, while being useless anywhere else. The
    designed grid never saw any of them and is correspondingly rough on them,
    while being roughly right across the whole range. With a piecewise-constant
    learner and a fixed budget of full-model runs, you get one or the other.
    """
    rows = []
    for pol in bh.SCENARIOS:
        agents, _ = run(pol, n=n, seed=42)
        truth = float(agents.frame["car_km"].mean())
        row = {"Scenario": pol.name, "Full model": truth}
        for label, sur in ((ENGINE_NARROW, narrow), (ENGINE_WIDE, wide)):
            pred = float(sur.predict(agents.frame, pol)["car_km"].mean())
            row[label] = pred
            row[f"{label} error %"] = (pred / truth - 1) * 100 if truth else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def extrapolation_test(surrogate: Surrogate, trained_on: list[bh.Policy] | None = None,
                       charges: tuple[float, ...] = CHARGE_SWEEP,
                       n: int = 1500) -> pd.DataFrame:
    """The harder question: does it hold on policies it was never shown?

    The full model is run at each parking charge and the surrogate is asked the
    same question. This is where a distilled surrogate is most likely to
    mislead, so it is measured rather than assumed.
    """
    trained_on = bh.SCENARIOS if trained_on is None else trained_on
    seen_charges = sorted({p.parking_charge_per_trip for p in trained_on})
    rows = []
    for charge in charges:
        pol = bh.Policy(f"parking {charge:.2f}", parking_charge_per_trip=charge)
        agents, _ = run(pol, n=n, seed=7)
        pred = surrogate.predict(agents.frame, pol)
        seen = any(abs(s - charge) < 1e-9 for s in seen_charges)
        rows.append({
            "parking_charge": charge,
            "full_model": float(agents.frame["car_km"].mean()),
            "surrogate": float(pred["car_km"].mean()),
            "seen_in_training": "trained on" if seen else "never seen",
        })
    out = pd.DataFrame(rows)
    out["error_pct"] = (out["surrogate"] / out["full_model"] - 1) * 100
    return out


def coverage_comparison(narrow: Surrogate, wide: Surrogate,
                        narrow_policies: list[bh.Policy] | None = None,
                        wide_policies: list[bh.Policy] | None = None,
                        n: int = 1200) -> pd.DataFrame:
    """Both surrogates and the truth, on one long frame ready to plot.

    The point of the comparison is not that one model is better than the other.
    It is that the same algorithm, given the same number of training rows,
    either tracks the full model or steps through it like a staircase depending
    entirely on how the *training policies* were chosen. Coverage of the input
    space is the thing that matters, and it is easy to get wrong without
    noticing, because both surrogates score R² = 1.0 on their own training data.
    """
    a = extrapolation_test(narrow, narrow_policies, n=n)
    b = extrapolation_test(wide, wide_policies, n=n)

    rows = []
    for charge, truth in zip(a["parking_charge"], a["full_model"]):
        rows.append({"parking_charge": charge, "car_km": truth,
                     "engine": ENGINE_FULL})
    for charge, v in zip(a["parking_charge"], a["surrogate"]):
        rows.append({"parking_charge": charge, "car_km": v,
                     "engine": ENGINE_NARROW})
    for charge, v in zip(b["parking_charge"], b["surrogate"]):
        rows.append({"parking_charge": charge, "car_km": v,
                     "engine": ENGINE_WIDE})
    return pd.DataFrame(rows)


# Named once, because the chart's colour scale and its legend both key off them.
ENGINE_FULL = "Full model"
ENGINE_NARROW = "Surrogate, 6 named scenarios"
ENGINE_WIDE = "Surrogate, designed grid"


def _median_seconds(fn, repeats: int = 3) -> float:
    """Median of a few runs, after one throwaway.

    A single `perf_counter` around a fast call measures the machine's mood as
    much as the code: the first call pays for allocation and warm caches, and
    on a shared cloud instance any one run can be twice its neighbours. The
    first version of the location benchmark reported the surrogate taking three
    times longer at 800 locations than at 200, which is impossible — it never
    sees the locations. That was noise being plotted as a finding.
    """
    fn()
    times = []
    for _ in range(repeats):
        started = time.perf_counter()
        fn()
        times.append(time.perf_counter() - started)
    return float(np.median(times))


def scaling_benchmark(surrogate: Surrogate,
                      sizes: tuple[int, ...] = (1_000, 10_000, 100_000, 1_000_000),
                      n_rings: int = 12) -> pd.DataFrame:
    """Time both engines as the population grows, at a fixed number of locations."""
    rows = []
    for n in sizes:
        pol = bh.Policy("benchmark")
        agents = bh.households(n, seed=3)
        # One repeat at a million households: the timing is stable there anyway
        # and three extra runs is a minute of nobody's time well spent.
        repeats = 1 if n >= 1_000_000 else 3

        surrogate_s = _median_seconds(lambda: surrogate.predict(agents, pol), repeats)
        full_s = _median_seconds(lambda: run(pol, n=n, seed=3, n_rings=n_rings), repeats)

        rows.append({
            "households": n,
            "surrogate_seconds": surrogate_s,
            "full_seconds": full_s,
            "speedup": full_s / surrogate_s,
        })
    return pd.DataFrame(rows)


def location_benchmark(surrogate: Surrogate, n: int = 4_000,
                       ring_counts: tuple[int, ...] = (12, 50, 200, 800, 2_000),
                       ) -> pd.DataFrame:
    """Time both engines as the number of *locations* grows.

    This is the benchmark that decides whether a distilled surrogate is worth
    having, and it is the one that gets left out. The full model's cost is
    households × locations × rounds; the surrogate's is one pass over
    households and does not know how many locations there were. So the margin
    between them is not a property of the population — it is a property of how
    finely the city is cut up. Twelve concentric rings is a caricature. A real
    study uses census output areas, and Enschede has on the order of a thousand.
    """
    rows = []
    for k in ring_counts:
        pol = bh.Policy("benchmark")
        agents = bh.households(n, seed=3)

        surrogate_s = _median_seconds(lambda: surrogate.predict(agents, pol))
        full_s = _median_seconds(lambda: run(pol, n=n, seed=3, n_rings=k))

        rows.append({
            "locations": k,
            "surrogate_seconds": surrogate_s,
            "full_seconds": full_s,
            "speedup": full_s / surrogate_s,
        })
    return pd.DataFrame(rows)
