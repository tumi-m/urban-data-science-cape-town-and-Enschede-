"""Households that choose, rather than cells that fill.

The growth simulation already in this project allocates people to land by a
rule. Nobody in it decides anything: there is no rent, no budget, no trade-off
between a cheaper house and a longer commute. That is why its own page says it
has "no land market, no developer behaviour, no feedback from prices to
demand", and why the only defensible output there is the difference between two
runs.

This module is the missing half. Households have incomes and a value of time.
Locations have rents. Each household picks a location, and then a way of
getting to work, by comparing what the options are worth to it — and rents move
until the demand for each location matches what is there. So the outputs
respond to policy: raise parking charges and mode shares move, which moves
car-kilometres, which moves the nitrogen figure that the constraint sections
show is what actually blocks building.

The method is standard and old. Random-utility discrete choice is McFadden;
rents clearing against location demand is Alonso-Muth-Mills bid rent; the two
combined are the core of UrbanSim. Nothing here is novel, and calling it novel
would be the easiest way to oversell it.

**All of it runs on synthetic households and a synthetic rent surface.** The
behavioural parameters are typical values from the choice-modelling literature
rather than estimates from Dutch travel-survey data. So the *direction* and
rough size of each response is meaningful; the levels are not. Fit the location
and mode models on ODiN and the same code becomes real.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Behavioural parameters
# ---------------------------------------------------------------------
#
# Stated here rather than buried, because every result below is a consequence
# of them. Values are conventional ones from the discrete-choice literature,
# not estimates from local data.

VALUE_OF_TIME = {          # € per hour, by income group
    "Lower income": 6.0,
    "Middle income": 11.0,
    "Higher income": 20.0,
}

INCOME = {                 # € per year, household
    "Lower income": 24_000,
    "Middle income": 45_000,
    "Higher income": 85_000,
}

RENT_BUDGET_SHARE = 0.30   # share of income a household will spend on housing

# Logit scale. Lower means choices are more sharply determined by utility;
# higher means more of the decision is unobserved. 1.0 is a neutral default.
LOGIT_SCALE = 1.0

MODES = {
    #                speed  €/km  fixed €/trip  needs_car  hill_penalty_min_per_100m
    "Walk":         dict(speed=4.5,  cost_km=0.0,  fixed=0.0,  car=False, hill=1.2),
    "Bicycle":      dict(speed=15.0, cost_km=0.0,  fixed=0.0,  car=False, hill=2.4),
    "Electric bike":dict(speed=20.0, cost_km=0.01, fixed=0.0,  car=False, hill=0.2),
    "Bus or train": dict(speed=22.0, cost_km=0.16, fixed=0.0,  car=False, hill=0.0),
    "Car":          dict(speed=30.0, cost_km=0.22, fixed=0.0,  car=True,  hill=0.0),
}

# Mode-specific constants absorb everything generalised cost does not capture:
# comfort, weather, status, the bother of parking, the fact that a bicycle in
# the Netherlands is simply what you use. They are not guessable — guessing
# them produced a base case with a 0.1% car share — so they are calibrated to
# reproduce an observed commuting split, which is what these constants are for.
#
# The target is roughly Enschede's commuting mode split: a cycling city, but
# one where the car still carries the largest single share of commute trips.
BASE_MODE_SPLIT = {
    "Walk": 0.05,
    "Bicycle": 0.30,
    "Electric bike": 0.08,
    "Bus or train": 0.12,
    "Car": 0.45,
}

CALIBRATION_DISTANCE_KM = 4.0     # a typical commute within the city
CALIBRATION_VOT = 11.0            # the middle income group


def calibrate_constants(target: dict[str, float] | None = None) -> dict[str, float]:
    """Solve for the constants that reproduce the observed base split.

    With a logit, this is exact rather than a fit: at the reference trip the
    constant for each mode is log(target share) minus its generalised utility,
    up to a shared offset. Standard practice, and the only honest way to have
    a base case that matches reality without pretending the parameters were
    estimated.
    """
    target = target or BASE_MODE_SPLIT
    zero = {k: 0.0 for k in MODES}
    base_u = _raw_utilities(CALIBRATION_DISTANCE_KM, CALIBRATION_VOT,
                            Policy("calibration"), zero)
    consts = {k: LOGIT_SCALE * np.log(target[k]) - base_u[k] for k in MODES}
    mean = np.mean(list(consts.values()))
    return {k: v - mean for k, v in consts.items()}


MODE_CONSTANT: dict[str, float] = {}     # filled in below, once Policy exists

# Enschede's ridge, as a number the mode choice can feel: metres of climb on a
# typical cross-town trip. This is the link back to the mobility section — the
# hill is why the plain bicycle loses to the car on longer trips, and why
# assistance changes the answer.
TYPICAL_CLIMB_M = 30.0

WORKING_DAYS = 220
TRIPS_PER_DAY = 2


@dataclass
class Policy:
    """The levers. Everything a city can actually pull, and nothing it cannot."""

    name: str = "Today"
    parking_charge_per_trip: float = 0.0    # € per car trip at the destination
    fuel_cost_multiplier: float = 1.0       # 1.0 = today's motoring cost
    ebike_subsidy: float = 0.0              # € per year off the cost of an e-bike
    transit_speed_multiplier: float = 1.0   # better frequency and priority
    car_ownership_cost: float = 2_400.0     # € per year to keep a car at all
    density_cap: float = 1.0                # 1.0 = today's permitted density
    note: str = ""


SCENARIOS = [
    Policy("Today", note="Current costs and current transit."),
    Policy("Parking priced", parking_charge_per_trip=2.50,
           note="€2.50 per car trip at the destination — a normal city-centre tariff."),
    Policy("E-bikes subsidised", ebike_subsidy=400.0,
           note="€400 a year off the cost of an electric bike, roughly a purchase subsidy "
                "spread over its life."),
    Policy("Better transit", transit_speed_multiplier=1.35,
           note="A third faster door to door, from frequency and priority rather than new track."),
    Policy("All three", parking_charge_per_trip=2.50, ebike_subsidy=400.0,
           transit_speed_multiplier=1.35,
           note="The three together, which is how they are actually available."),
    Policy("Motoring cheaper", fuel_cost_multiplier=0.7,
           note="The counterfactual worth having: what happens if driving gets cheaper."),
]


# ---------------------------------------------------------------------
# Agents and places
# ---------------------------------------------------------------------

def households(n: int = 3000, seed: int = 0) -> pd.DataFrame:
    """A synthetic population with incomes and a value of time.

    The income split is roughly the shape of a Dutch city with a large student
    population: a long lower tail, a thick middle, a thin top.
    """
    rng = np.random.default_rng(seed)
    groups = rng.choice(
        list(INCOME), size=n, p=[0.38, 0.45, 0.17])
    return pd.DataFrame({
        "group": groups,
        "income": [INCOME[g] for g in groups],
        "vot": [VALUE_OF_TIME[g] for g in groups],
        "rent_budget": [INCOME[g] * RENT_BUDGET_SHARE for g in groups],
    })


def locations(n_rings: int = 12, max_km: float = 6.0) -> pd.DataFrame:
    """Concentric bands at increasing distance from the centre.

    Rings rather than the full grid: location choice only needs distance to the
    centre and distance to a station, and a ring model makes the rent gradient —
    the thing the market clearing produces — directly readable.
    """
    edges = np.linspace(0.25, max_km, n_rings)
    # Land area of each ring grows with distance, which is what makes the outer
    # rings able to absorb more households than the inner ones.
    inner = np.concatenate([[0.0], edges[:-1]])
    area = np.pi * (edges**2 - inner**2)
    return pd.DataFrame({
        "ring": range(n_rings),
        "km_to_centre": edges,
        # Stations at 0 km and about 2.7 km out, as in the access section.
        "km_to_station": np.minimum(edges, np.abs(edges - 2.7)),
        "area_km2": area,
        "capacity": area * 1800,     # dwellings per km² at today's permitted density
    })


# ---------------------------------------------------------------------
# Mode choice
# ---------------------------------------------------------------------

def _raw_utilities(distance_km: float, vot: float, policy: Policy,
                   constants: dict[str, float] | None = None,
                   climb_m: float = TYPICAL_CLIMB_M) -> dict[str, float]:
    """Generalised cost of each mode, turned into a utility.

    Generalised cost is time priced at the household's value of time, plus the
    money it actually spends. The hill enters as extra minutes, which is how a
    gradient is felt: not as metres, but as effort and delay.
    """
    constants = MODE_CONSTANT if constants is None else constants
    out = {}
    for name, m in MODES.items():
        speed = m["speed"] * (policy.transit_speed_multiplier
                              if name == "Bus or train" else 1.0)
        minutes = 60 * distance_km / speed
        minutes += m["hill"] * (climb_m / 100)

        cost = m["cost_km"] * distance_km * (
            policy.fuel_cost_multiplier if m["car"] else 1.0)
        if m["car"]:
            cost += policy.parking_charge_per_trip
            # Ownership is deliberately NOT charged here. It is sunk once the
            # household owns a car, and mode choice compares marginal costs.
            # Spreading it over trips is a common and serious error: it prices
            # a car trip at several euro and the car then loses to a free
            # bicycle at every distance, which is not what anyone observes.
        if name == "Electric bike":
            cost -= policy.ebike_subsidy / (WORKING_DAYS * TRIPS_PER_DAY)

        generalised = (minutes / 60) * vot + cost
        out[name] = constants.get(name, 0.0) - generalised
    return out


def mode_utilities(distance_km: float, vot: float, policy: Policy,
                   climb_m: float = TYPICAL_CLIMB_M) -> dict[str, float]:
    """Utilities with the calibrated constants applied."""
    return _raw_utilities(distance_km, vot, policy, MODE_CONSTANT, climb_m)


MODE_CONSTANT.update(calibrate_constants())


def _softmax(u: np.ndarray, scale: float = LOGIT_SCALE) -> np.ndarray:
    z = u / scale
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def mode_utilities_array(distance_km, vot, policy: Policy,
                         climb_m: float = TYPICAL_CLIMB_M) -> np.ndarray:
    """The same utilities, over arrays of distances and values of time.

    Identical arithmetic to `_raw_utilities`, written to broadcast. It exists
    because the scalar version called once per household is the single slowest
    thing in this project, and a million households is the point of the
    scaling section. Modes are the last axis, in `MODES` order.
    """
    d = np.asarray(distance_km, dtype=float)
    v = np.asarray(vot, dtype=float)
    d, v = np.broadcast_arrays(d, v)
    out = np.empty(d.shape + (len(MODES),))

    for i, (name, m) in enumerate(MODES.items()):
        speed = m["speed"] * (policy.transit_speed_multiplier
                              if name == "Bus or train" else 1.0)
        minutes = 60 * d / speed + m["hill"] * (climb_m / 100)

        cost = m["cost_km"] * d * (policy.fuel_cost_multiplier if m["car"] else 1.0)
        if m["car"]:
            cost = cost + policy.parking_charge_per_trip
        if name == "Electric bike":
            cost = cost - policy.ebike_subsidy / (WORKING_DAYS * TRIPS_PER_DAY)

        out[..., i] = MODE_CONSTANT[name] - ((minutes / 60) * v + cost)
    return out


def mode_shares_array(distance_km, vot, policy: Policy) -> np.ndarray:
    """Logit shares over arrays. Modes on the last axis, in `MODES` order."""
    return _softmax(mode_utilities_array(distance_km, vot, policy))


def mode_shares(distance_km: float, vot: float, policy: Policy) -> dict[str, float]:
    """Probability of each mode. The logit is the model, not a tie-break."""
    u = mode_utilities(distance_km, vot, policy)
    names = list(u)
    p = _softmax(np.array([u[n] for n in names]))
    return dict(zip(names, p))


def expected_car_km(distance_km: float, vot: float, policy: Policy) -> float:
    """Car-kilometres a household is expected to drive per year for commuting."""
    p_car = mode_shares(distance_km, vot, policy)["Car"]
    return p_car * distance_km * 2 * TRIPS_PER_DAY / 2 * WORKING_DAYS


# ---------------------------------------------------------------------
# Location choice, with rents that clear
# ---------------------------------------------------------------------

@dataclass
class Outcome:
    policy: Policy
    rings: pd.DataFrame
    modes: pd.DataFrame
    by_group: pd.DataFrame
    mean_car_km: float
    nox_kg_per_household: float
    iterations: int = 0
    converged: bool = False
    history: list = field(default_factory=list)


NOX_G_PER_KM = 0.2          # fleet average, as in the nitrogen section


def simulate(policy: Policy, n_households: int = 3000, seed: int = 0,
             max_iter: int = 60, tol: float = 0.012) -> Outcome:
    """Place households, then let rents move until the market clears.

    Each round: households pick a ring by logit over (rent, commute cost,
    space); wherever demand exceeds capacity the rent rises, and where it falls
    short it drops. Repeat until nothing much moves. That is bid rent, done
    numerically because the closed form does not survive a real cost function.
    """
    hh = households(n_households, seed)
    rings = locations().copy()

    # Start from a flat rent and let the model find the gradient rather than
    # assuming one — the gradient is a result, not an input.
    rent = np.full(len(rings), 7_000.0)     # € per year
    dist = rings["km_to_centre"].to_numpy()
    capacity = rings["capacity"].to_numpy()
    capacity = capacity / capacity.sum() * n_households   # scaled to the population

    vot = hh["vot"].to_numpy()[:, None]
    budget = hh["rent_budget"].to_numpy()[:, None]

    # Annual commuting cost of living in each ring, per household.
    commute_cost = np.array([
        [_annual_commute_cost(d, v[0], policy) for d in dist] for v in vot
    ])

    history, converged, it = [], False, 0
    for it in range(1, max_iter + 1):
        # Utility of a ring: what is left after rent and commuting, plus a
        # preference for space further out, penalised if rent breaks the budget.
        residual = budget - rent[None, :] - commute_cost
        space = 0.18 * np.log1p(dist)[None, :]
        overspend = -3.0 * np.clip((rent[None, :] - budget) / budget, 0, None)
        u = residual / 10_000 + space + overspend

        p = _softmax(u)
        demand = p.sum(axis=0)

        gap = (demand - capacity) / np.maximum(capacity, 1)
        history.append(float(np.abs(gap).max()))
        if np.abs(gap).max() < tol:
            converged = True
            break
        # Rents move toward clearing. The damping keeps it from oscillating.
        rent = np.clip(rent * (1 + 0.28 * gap), 1_500, 60_000)

    rings["rent"] = rent
    rings["households"] = demand
    rings["share"] = demand / demand.sum()

    # Who ended up where, and what they do about getting to work.
    group_rows, mode_totals = [], {m: 0.0 for m in MODES}
    total_car_km = 0.0
    for g in INCOME:
        mask = (hh["group"] == g).to_numpy()
        if not mask.any():
            continue
        pg = p[mask].mean(axis=0)
        mean_dist = float((pg * dist).sum())
        v = VALUE_OF_TIME[g]
        shares = mode_shares(mean_dist, v, policy)
        car_km = sum(
            _annual_car_km(d, v, policy) * w for d, w in zip(dist, pg))
        group_rows.append({
            "group": g, "mean_km_to_centre": mean_dist,
            "mean_rent": float((pg * rent).sum()),
            "car_km_per_year": car_km,
            **{f"share_{k}": v2 for k, v2 in shares.items()},
        })
        weight = mask.sum() / len(hh)
        for k, v2 in shares.items():
            mode_totals[k] += v2 * weight
        total_car_km += car_km * weight

    modes = pd.DataFrame(
        [{"mode": k, "share": v} for k, v in mode_totals.items()]
    ).sort_values("share", ascending=False)

    nox = total_car_km * NOX_G_PER_KM / 1000
    return Outcome(policy, rings, modes, pd.DataFrame(group_rows),
                   total_car_km, nox, it, converged, history)


def _annual_commute_cost(distance_km: float, vot: float, policy: Policy) -> float:
    """Expected annual generalised cost of commuting from a given distance.

    The logsum of the mode choice — the standard way a lower-level choice
    feeds the level above it, and the reason improving transit makes a distant
    ring more attractive rather than only shifting its mode split.
    """
    u = np.array(list(mode_utilities(distance_km, vot, policy).values()))
    logsum = LOGIT_SCALE * np.log(np.exp((u - u.max()) / LOGIT_SCALE).sum()) + u.max()
    trips = WORKING_DAYS * TRIPS_PER_DAY
    return -logsum * trips


def _annual_car_km(distance_km: float, vot: float, policy: Policy) -> float:
    p_car = mode_shares(distance_km, vot, policy)["Car"]
    return p_car * distance_km * WORKING_DAYS * TRIPS_PER_DAY


def run_all(n_households: int = 3000) -> tuple[pd.DataFrame, dict[str, Outcome]]:
    """Every scenario, with the summary table the section is built around."""
    outcomes, rows = {}, []
    base = None
    for pol in SCENARIOS:
        o = simulate(pol, n_households)
        outcomes[pol.name] = o
        if base is None:
            base = o
        rows.append({
            "Scenario": pol.name,
            "Car share": float(o.modes.set_index("mode").loc["Car", "share"]),
            "Bike + e-bike": float(
                o.modes.set_index("mode").loc[["Bicycle", "Electric bike"], "share"].sum()),
            "Transit share": float(o.modes.set_index("mode").loc["Bus or train", "share"]),
            "Car km per household": o.mean_car_km,
            "NOx kg per household": o.nox_kg_per_household,
            "vs today": (o.mean_car_km / base.mean_car_km - 1) if base else 0.0,
            "Note": pol.note,
        })
    return pd.DataFrame(rows), outcomes


def elasticity_curve(lever: str, values: np.ndarray,
                     n_households: int = 1500) -> pd.DataFrame:
    """Sweep one lever and watch car use respond.

    A single scenario tells you an outcome. A sweep tells you the shape of the
    response, which is the part that transfers to a city that is not this one.
    """
    rows = []
    for v in values:
        pol = Policy("sweep")
        setattr(pol, lever, float(v))
        o = simulate(pol, n_households)
        rows.append({
            "value": float(v),
            "car_km": o.mean_car_km,
            "car_share": float(o.modes.set_index("mode").loc["Car", "share"]),
            "nox_kg": o.nox_kg_per_household,
        })
    return pd.DataFrame(rows)
