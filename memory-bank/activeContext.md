# Active context — what we're doing right now

## Phase 0 — Bootstrap: CLOSED
Scaffold, `.clinerules/`, memory bank, `make check` gate, `io.py`/`peek.py`,
both guard tests: all green. See progress.md for the ledger.

## Next: Phase 1 — Data layer (12 ingest tasks, one per task)
1. ~~Link sweep~~ **DONE** — results in dataCatalogue.md. Four follow-ups
   before ingests: (a) CT dam-levels PDF URL is 503 → find current dashboard
   URL; (b) confirm MyCiTi GTFS location; (c) retry Klimaatmonitor from a
   networked machine; (d) DWS hydrology 403s to bots → manual/alt endpoint.
2. Ingest order: `za_census_2022_smallarea` → `nl_cbs_wijkbuurt` →
   `ct_dam_levels_weekly` → `eskom_eaf_stages` → `nl_klimaatmonitor_energy` →
   `nl_odin_mobility` → `ct_transit_gtfs` → `ct_minibus_routes` (the hard one,
   1.5 tasks, WIMT licence check) → `patents_epo_regional` →
   `openalex_institutions` → `ghsl_builtup_timeseries` → `osm_networks_metrics`.
3. Each via `/new-dataset` workflow; idempotent; sidecar complete or
   "UNVERIFIED — do not publish"; append one line to dataCatalogue.md.

## Standing cautions
- **Network IS available in this sandbox** (curl/httpx reach CBS, OpenAlex API,
  etc. — 200s). The earlier "no outbound network" note is outdated. Some hosts
  still block bots (DWS 403, openalex.org HTML 403) or time out (Klimaatmonitor).
- WIMT taxi data licence may block publication — fallback is OSM
  `route=share_taxi` + rank surveys, loudly caveated.
- EPO OPS free tier is rate-limited: cache every response to `data/raw/`.
