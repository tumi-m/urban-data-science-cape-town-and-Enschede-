# Data catalogue — one line per curated dataset

| name | publisher | unit | period | rows | licence | caveat |
|------|-----------|------|--------|------|---------|--------|
| za_census_2022_smallarea | Statistics South Africa | national + municipality | 2011–2022 | 9 | Stats SA open data (Statistics Act 6 of 1999) | small-area counts NOT bulk-downloadable (SuperWEB2/ISIbalo only); 2022 municipal count not bulk-published — 2011 CCT baseline only |
| _(next: nl_cbs_wijkbuurt, ct_dam_levels_weekly, eskom_eaf_stages, nl_klimaatmonitor_energy, nl_odin_mobility, ct_transit_gtfs, ct_minibus_routes, patents_epo_regional, openalex_institutions, ghsl_builtup_timeseries, osm_networks_metrics)_ | | | | | | |

## Link sweep — 2026-08-16 (Phase 1 task 1, DONE)

Resolved every source URL in plan §5.1. Status per source:

| # | source | status | resolved URL / note |
|---|--------|--------|--------------------|
| 1 | City of Cape Town ODP | ✅ 200 | https://odp-cctegis.opendata.arcgis.com/ — ArcGIS Hub; use per-layer REST/GeoJSON, not scraping |
| 2 | Stats SA | ✅ 200 | https://www.statssa.gov.za/ — Census 2022 small-area via SuperWEB2 / ISIbalo portal |
| 3 | MyCiTi GTFS | ⚠️ not yet located | check ODP first, fall back to operator; no stable URL confirmed |
| 4 | WIMT minibus taxi | ⚠️ licence check pending | WIMT terms changed; fallback OSM `route=share_taxi` + rank surveys |
| 5 | DWS hydrology | ⚠️ 403 to bots | https://www.dws.gov.za/hydrology/ — site up, anti-scraper block; verify manually / alt endpoint |
| 5b | CT dam levels (City PDF) | ❌ 503 | plan URL stale — find current dam-levels dashboard URL before ingest |
| 5c | capetowndamlevels.co.za | ✅ 200 | https://capetowndamlevels.co.za/data-sources/ — documents its own chain |
| 6 | Eskom Data Portal | ✅ 200 | https://www.eskom.co.za/dataportal/ — 5-year windows, email-delivered download |
| 8 | CBS StatLine | ✅ 200 | https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data — OData, `cbsodata` client |
| 9 | ODiN mobility | ✅ 200 | https://data.overheid.nl/en/dataset/26253-… — CC-BY 4.0; OData table 84710ENG; 2024 methodological break noted |
| 10 | PDOK | ✅ 200 | https://www.pdok.nl/ — OGC APIs + downloads |
| 11 | Klimaatmonitor | ⚠️ timeout | https://klimaatmonitor.databank.nl/ — connection timed out from sandbox; retry on networked machine |
| 11b | Transitiedata | ✅ 200 | https://www.transitiedata.nl/ — free maps, paid exact values; per-buurt energy data |
| 12 | Kennispark Twente | ✅ 200 | https://kennispark.nl/en/kennispark/ — "900+ spin-offs" published figure; hand-curate CSV |
| 13 | EPO OPS | ✅ 200 | https://developers.epo.org/ — OAuth2 key/secret; cache every response |
| 14 | PATSTAT | ✅ (via WIPO manual) | ~90M records, €1250/yr or 2-month free trial; OECD REGPAT free on request |
| 15 | OpenAlex | ✅ 200 (API) | https://api.openalex.org/ — HTML site 403s to bots, API is the ingest path |
| 16 | WIPO manual | ✅ 200 | https://wipo-analytics.github.io/manual/databases.html |
| 17 | GHSL | ✅ 200 | https://human-settlement.emergency.copernicus.eu/datasets.php — R2023A, 1975–2030 |
| 18 | WorldPop | ✅ 200 | https://www.worldpop.org/ — Global 2, 100 m |
| 19 | Overture Maps | ✅ 200 | https://overturemaps.org/ — buildings/places |
| 20 | Open-Meteo | ✅ 200 | https://open-meteo.com/ — CC BY 4.0, no key, ERA5 from 1940 |

**Actions before ingests:** (a) locate current CT dam-levels dashboard URL (plan's
PDF URL is 503); (b) confirm MyCiTi GTFS location; (c) retry Klimaatmonitor from
a networked machine; (d) DWS hydrology needs a manual/browser fetch or alternate
endpoint — do not block the water thread on it, capetowndamlevels.co.za documents
a usable chain.
