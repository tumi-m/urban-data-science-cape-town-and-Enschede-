# Active context — what we're doing right now

## Phase 0 — Bootstrap: CLOSED
Scaffold, `.clinerules/`, memory bank, `make check` gate, `io.py`/`peek.py`,
both guard tests: all green. See progress.md for the ledger.

## Next: Phase 1 — Data layer (12 ingest tasks, one per task)
1. **Link sweep first** (10k tokens): resolve every URL in plan §5.1, record
   final resolved URLs in dataCatalogue.md, flag 404s. Government portals
   move; doing this later costs a full task.
2. Then ingests in dependency order: `za_census_2022_smallarea` →
   `nl_cbs_wijkbuurt` → `ct_dam_levels_weekly` → `eskom_eaf_stages` →
   `nl_klimaatmonitor_energy` → `nl_odin_mobility` → `ct_transit_gtfs` →
   `ct_minibus_routes` (the hard one, 1.5 tasks, WIMT licence check) →
   `patents_epo_regional` → `openalex_institutions` →
   `ghsl_builtup_timeseries` → `osm_networks_metrics`.
3. Each via `/new-dataset` workflow; idempotent; sidecar complete or
   "UNVERIFIED — do not publish"; append one line to dataCatalogue.md.

## Standing cautions
- This sandbox has no general outbound network: run `fetch()` on a networked
  machine, `build()` runs offline from cached raw.
- WIMT taxi data licence may block publication — fallback is OSM
  `route=share_taxi` + rank surveys, loudly caveated.
- EPO OPS free tier is rate-limited: cache every response to `data/raw/`.
