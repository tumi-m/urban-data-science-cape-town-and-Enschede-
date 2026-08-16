# KINETIEK — project brief (one page)

An urban data science project on Cape Town and Enschede. Deployed on
Streamlit Community Cloud. Budget: 2,000,000 tokens ≈ 50 tasks.

**Thesis:** two cities, the same object at wildly different scale, running
opposite experiments. Cape Town (~4.8M): can an informal system outperform a
planned one under constraint? Enschede (~160k): a completed experiment in
reindustrialising around knowledge after losing its textiles industry. Each
is the other's control group. The comparison is **rates, not levels**.

**Five threads:** mobility & flows · knowledge & IP · nature & metabolism ·
energy · prediction & simulation (the falsifiable binder).

**Method:** every essay resolves to a Meadows diagram — a named stock, flow,
delay, loop, and leverage point (rank on the twelve-place hierarchy).

**Comparator cities** (only where they change a conclusion): Nairobi, Bogotá,
Curitiba, Groningen, Houten, Eindhoven, Singapore, Detroit, Pittsburgh.

## Architecture in one line
All heavy computation offline; the app reads precomputed parquet artefacts
only (Streamlit Cloud ~1 GB RAM, hibernates after 12 h idle; curated data
< 25 MB; maps pre-simplified GeoParquet via pydeck).

## Three contracts
1. **Data:** every `data/curated/*.parquet` has a `.meta.json` sidecar
   (source, licence, sha256, caveats). Guard test enforces it. Licence
   unverifiable → "UNVERIFIED — do not publish" or it ships nowhere.
2. **Figure:** one pure function per figure (`fig_<id>_<slug>() -> alt.Chart`),
   registered in `FIGURES`, source + as_of in subtitle.
3. **Prose:** no number as a literal — every numeral in `essays/*.md` is
   `{{metric:name}}` or `{{fig:id}}`. Guard test enforces it. This makes
   accidental hallucinated statistics structurally impossible.

## Phase order (gated; close each with /phase-close)
0 Bootstrap (60k) → 1 Data layer, 12 ingests (420k) → 2 Metrics, ~40 figures,
14 essays (480k) → 3 Simulation, 4–5 SD models pre-solved offline (400k) →
4 Streamlit app + deploy (340k) → 5 Audit & harden (100k) + 200k reserve.

## What makes this different from a dashboard
It commits (dated falsifiable predictions in `predictions.yaml` with a public
Brier score). It cannot lie by accident (numbers trace through tested
functions to checksummed files to cited sources). It explains rather than
displays (stock/flow/delay/loop per essay).

**Coexistence note:** this repo also contains the earlier project
(`urban/`, `streamlit_app.py`, Next.js `app/`). KINETIEK lives in `src/`,
`essays/`, `data/curated/`, and `app/pages/` (Streamlit entry: `app/Home.py`,
Phase 4). `make check` scopes lint/types to the new layer.
