# Data contract

## Every curated file has a sidecar
`data/curated/<name>.parquet` requires `data/curated/<name>.meta.json`:

```json
{
  "name": "...", "source_url": "...", "publisher": "...",
  "licence": "...", "retrieved_at": "ISO-8601Z", "sha256": "...",
  "rows": 0, "columns": {"col": "dtype"}, "spatial_unit": "...",
  "temporal_range": ["start", "end"], "caveats": ["..."], "refresh": "..."
}
```

`tests/test_contracts.py` fails the build if any curated parquet lacks a
sidecar, if `sha256` mismatches, or if `licence` is empty.

## Licence discipline
"Free to access" is not "free to redistribute". If the licence cannot be
determined, write `"UNVERIFIED — do not publish"` in the sidecar and log it in
`memory-bank/progress.md`. Never guess a licence. Phase 5 audit pulls anything
still UNVERIFIED from the public build. There is no third option.

## Directory rules
- `data/raw/` — gitignored, immutable, never read by the agent directly.
- `data/interim/` — gitignored scratch.
- `data/curated/` — committed, < 25 MB total, always with sidecars.
- Anything larger ships as a GitHub Release asset fetched behind
  `@st.cache_data(ttl=86400)`.

## Provenance page
`app/pages/8_Provenance.py` renders straight from the sidecars. Ship the
caveats. The sidecar is the single source of truth for what the data is.

## Reading data
Only via `kinetiek.io.load_curated(name)` (verifies sidecar + sha256).
Never inspect data by reading files — use `python -m kinetiek.peek <name>`.
