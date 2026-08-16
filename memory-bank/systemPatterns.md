# System patterns — the three contracts

## 1. Data contract
Every `data/curated/<name>.parquet` has a sibling `<name>.meta.json`:

```json
{
  "name": "ct_dam_levels_weekly",
  "source_url": "https://www.dws.gov.za/hydrology/",
  "publisher": "Department of Water and Sanitation (ZA)",
  "licence": "Open Government Licence — verify before publishing",
  "retrieved_at": "2026-08-20T18:40:00Z",
  "sha256": "…",
  "rows": 1044,
  "columns": {"week_end": "date", "dam": "str", "pct_full": "float64"},
  "spatial_unit": "dam",
  "temporal_range": ["2006-01-01", "2026-08-10"],
  "caveats": ["Theewaterskloof gauge recalibrated 2019-03; pre/post not strictly comparable"],
  "refresh": "weekly"
}
```

`tests/test_contracts.py` fails the build on: missing sidecar, sha256
mismatch, empty licence. Ingest pattern: `fetch()` (download to
`data/raw/<name>/`, skip if present) + `build()` (raw → curated parquet +
sidecar), both idempotent. Reading is only via
`kinetiek.io.load_curated(name)`.

## 2. Figure contract
One function per figure: `src/kinetiek/figures/` → `fig_<id>_<slug>()`
returning `alt.Chart`. Pure — no I/O beyond `load_curated`. House theme
registered as `kinetiek`. Subtitle carries `source`, `note`, `as_of`.
Registered in `FIGURES: dict[str, Callable]`; essays and app pages resolve
by ID. 2x PNG to `build/figures/<id>.png` at build time.

## 3. Model contract
Each SD model in `src/kinetiek/models/sd/` exposes:
- `stocks() -> dict[str, float]` — initial conditions with units
- `flows(t, y, p) -> dict[str, float]` — every flow named, units in docstring
- `loops() -> list[Loop]` — polarity and delay, for the auto-diagram
- `simulate(p, years) -> pl.DataFrame`
- `calibrate.py`: fit on the training window, report holdout RMSE **next to a
  naive persistence baseline**. If it loses to persistence, say so on the
  page. Losing is a finding; hiding it is a failure.
- Pre-solved on a parameter grid offline → `data/curated/<name>_grid.parquet`
  (< 5 MB, coarsen the grid, never drop the sidecar). The app interpolates;
  nothing integrates at request time.

## Prose contract (the anti-hallucination rule)
No number may appear in an essay as a literal. Every number is
`{{metric:<name>}}` resolved at build time by a named, tested metric function
in `src/kinetiek/metrics/` — the ONLY source of numbers in prose.
`tests/test_no_bare_numbers.py` fails on any numeral outside `{{…}}`
directives, except 4-digit years 1800–2100, or a line ending in `<!-- lit -->`
(use must be logged in progress.md; fixing by allowlist instead of a metric
function is prohibited).
