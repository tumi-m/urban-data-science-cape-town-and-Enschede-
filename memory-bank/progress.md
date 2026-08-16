# Progress — phase status + token ledger

| phase | status | acceptance |
|-------|--------|------------|
| 0 Bootstrap | CLOSED | make check green; .clineignore verified; ledger ≤ 60k |
| 1 Data layer (12 ingests) | not started | tripwire: 550k cumulative → cut to 6 datasets, defer rest to v2 |
| 2 Metrics, figures, essays | not started | tripwire: 1.05M → cut to 10 essays |
| 3 Simulation layer | not started | tripwire: 1.5M → 3 SD models, drop the ABM |
| 4 Streamlit app | not started | tripwire: 1.8M → drop Explorer, keep static maps |
| 5 Audit & harden | not started | reserve untouchable until Phase 4 closes |

## Token ledger

| task | phase | in | out | cum | note |
|------|-------|---:|----:|----:|------|
| phase0-audit | 0 | ~14k | ~6k | ~20k | repo audit: nothing pre-existing to skip |
| phase0-scaffold | 0 | ~8k | ~4k | ~32k | T0.1 mkdir tree, .clineignore, pinned requirements, deps installed |
| phase0-rules | 0 | ~6k | ~7k | ~45k | T0.2 six .clinerules files, hand-written |
| phase0-memory-bank | 0 | ~4k | ~5k | ~54k | T0.3 seven memory-bank files seeded |
| phase0-gate | 0 | ~5k | ~4k | ~63k | T0.4 io.py, peek.py, guard tests, Makefile, make check green |

Phase 0 closes slightly over the 60k soft budget (~63k est.), under the 90k
tripwire. Cause: full repo-state audit required first (user directive: skip
nothing already done). No corrective action.

## Scope notes
- `osmnx` deferred from requirements.txt to Phase 3 (offline scripts only) —
  heavy dependency tree, unneeded until network-metrics task.
- requirements.txt pins include the pre-existing project's deps (streamlit,
  altair, pandas, sklearn, geopandas, shapely, pyproj, pytest) at resolved
  versions, because the earlier project shares this environment.
