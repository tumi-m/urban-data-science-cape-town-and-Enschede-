# Project — KINETIEK

## Thesis
Two cities, the same object at wildly different scale, running opposite
experiments. Cape Town (~4.8M): informal system under constraint, testing
whether emergence outperforms planning. Enschede (~160k): completed experiment
in reindustrialising around knowledge after losing its industry.

The comparison is **rates**, not levels: how fast each city converts inputs
into movement, inventions, water, and watts — and what governs the rate.
Not "rich vs poor". Each city is the other's control group.

## Five threads
1. Mobility & flows — movement as the primary observable
2. Knowledge & IP creation — patents, spinouts, co-invention networks
3. Nature & metabolism — water, heat, green, waste, per person per day
4. Energy — load shedding vs gas phase-out; opposite failure modes
5. Prediction & simulation — the falsifiable method binding the four

## Method: stocks, flows, delays, loops
Every essay resolves to a Meadows diagram naming its leverage point (rank on
Meadows' twelve-place hierarchy). No stock + flow + delay + loop = not
finished, just journalism.

## Comparator cities
Nairobi (informal transit), Bogotá/Curitiba (BRT economics), Groningen/Houten
(cycling ceiling), Eindhoven (patent tail), Singapore (pricing), Detroit/
Pittsburgh (shrinking-city reindustrialisation). **Rule: a comparator may
enter a chart only if it changes the reader's conclusion.**

## What "done" means
A phase is done when its acceptance criteria in the implementation plan pass
and `make check` is green. An essay is done when every number resolves through
a tested metric and it names its leverage point. A model is done when its
holdout RMSE is reported next to a naive baseline — including when it loses.

## Non-negotiables
- All heavy computation offline; the Streamlit app only reads precomputed
  artefacts (Streamlit Cloud: ~1 GB RAM, hibernates after 12 h idle).
- Committed curated data < 25 MB total.
- No number in prose except via `{{metric:...}}`.
- Commit after every task. One task = one deliverable.
