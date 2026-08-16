# Product context — who reads this, why it exists

## Readers
- **Urban-data practitioners** who want to see method done honestly:
  calibrated models with holdout scores, provenance on every number.
- **Policy-curious readers** of the Dediu/Evans school: one chart, one claim,
  rates over levels, falsifiers stated up front.
- **The author, later.** The predictions page is a self-audit device: a
  prediction page with no resolved-and-wrong entries after two years is a
  page that isn't predicting anything.

## Why it exists
Most urban data projects produce dashboards: many charts, no claims, no
falsifiers, no consequences. KINETIEK has three properties a dashboard does
not:

1. **It commits.** `predictions.yaml` carries dated, resolvable claims with
   priors and a running Brier score. The project can be wrong in a way
   anyone can check.
2. **It cannot lie by accident.** Every number in every sentence traces
   through a tested metric function to a checksummed curated file to a cited
   source. The build fails otherwise — unusual, cheap, and the single best
   thing about a project written largely by a language model.
3. **It explains rather than displays.** Every essay names a stock, a flow,
   a delay, a loop, and a leverage point. A claim about *why* a city behaves
   as it does — the only thing worth writing.

## Product surface
A Streamlit app: Home (thesis + three headline charts), five thread pages
(Motion, Making, Metabolism, Power, Simulator), Explorer, Predictions, and a
non-negotiable Provenance page rendering straight from the data sidecars.

## What it is not
Not "rich city vs poor city" — that comparison is boring and already made.
Not a two-disconnected-city-reports pair: every essay has at least one figure
with both cities on the same axes.
