# Tech context

## Hard platform constraint
**Streamlit Community Cloud: ~1 GB RAM, hibernates after 12 h without
traffic.** Therefore: all heavy computation happens offline; the app only
reads precomputed artefacts. No model fitting, network routing, or raster
processing at request time. The app loads parquet, renders Altair, runs
sub-second arithmetic on precomputed coefficient tables.

Corollaries:
- Committed curated data < 25 MB. Larger → GitHub Release asset, fetched
  behind `@st.cache_data(ttl=86400)`.
- Simulation pages read pre-solved parameter grids, interpolate in-app.
  Never `solve_ivp` at request time.
- Maps: pre-simplified GeoParquet, pydeck rendering, `geopandas` never
  imported by `app/`. Full-precision OSM never committed.
- Cold start target < 10 s; memory < 400 MB before data loads.

## Stack (pinned in requirements.txt; Python 3.11+)
polars (data), pyarrow, duckdb, altair (charts) + `kinetiek` theme,
pydeck (maps), networkx (graph metrics), scipy/numpy (models:
`solve_ivp` stock/flow functions, not a Vensim library), scikit-learn,
geopandas/shapely/pyproj (offline ingest only), pyyaml (predictions.yaml),
requests/httpx. `osmnx` deferred to Phase 3 offline scripts.

## Tooling
- `make check` = ruff + mypy (scoped to `src/`, `tests/`) + pytest
  `-q --tb=line`. The only verification command.
- Entry points: `python -m kinetiek.ingest.<name>`, `python -m kinetiek.peek
  <name>` (bounded output, ≤ 40 lines).
- Secrets in `.streamlit/secrets.toml` (gitignored). The app should need
  none — all ingestion is offline. A page needing a secret is doing
  something wrong.

## Sandbox note
This dev container has no general outbound network to data portals; live
fetches happen at build time on a networked machine or CI. Ingest modules
must therefore be cleanly separated (`fetch()` vs `build()`) so `build()` can
run from cached raw data without the network.
