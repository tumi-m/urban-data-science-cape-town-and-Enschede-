# Python style, typing, deps, testing

## Layout
- `src/kinetiek/` is a package; ingest modules are `kinetiek.ingest.<name>`.
- Entry points: `python -m kinetiek.ingest.<name>`, `python -m kinetiek.peek <name>`.
- All analysis code in `src/`; the app (`app/`) imports, never computes.

## Style
- Python 3.11+ syntax, `from __future__ import annotations` in every module.
- Type hints on all public functions. Docstrings state units.
- polars for data (pandas only where a library forces it); numpy for math.
- One function per figure, one module per ingest source, one metric per number.
- Idempotent ingest: re-running a fetch with data present is a no-op.

## Dependencies
- Only what `requirements.txt` pins. Anything new requires a memory-bank note
  explaining why (Streamlit Cloud's 1 GB is spent mostly on imports).
- `geopandas` never imported inside `app/` — precompute to GeoParquet, render
  with pydeck. Heavy engines (r5py, JVM) live in `scripts/`, never `src/`.

## Testing
- `pytest -q --tb=line -x`. Test output must stay short.
- Metrics: unit tests with hand-checked expected values.
- Models: mass balance, non-negative stocks, holdout RMSE vs naive baseline.
- Contracts: `tests/test_contracts.py` (sidecars + sha256 + licence) and
  `tests/test_no_bare_numbers.py` (essays) are guard tests. Never weaken them.

## Verification
`make check` is the only verification command. If it is red, the task is not
done. Report the summary line, not tracebacks.
