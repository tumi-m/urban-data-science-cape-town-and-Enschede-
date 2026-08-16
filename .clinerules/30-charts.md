# Chart grammar (Altair house theme)

## One chart, one claim
If a chart makes two points, it is two charts. The accent colour carries the
claim; everything else is muted.

## Fixed colours
Cape Town and Enschede get fixed colours across **every** chart in the
project — the reader should never have to check a legend.

## Kill the legend
Direct-label series at their ends. No gridlines except a single zero line.

## Scales
- Log scales when comparing growth rates — and say so in the subtitle.
- Index to 100 at a stated base year when comparing trajectories at different
  scale. This is the single most useful move for a 4.8M city against a 160k
  one. (Enschede vs Cape Town must be indexed or per-capita, always.)

## Figure contract
- One function per figure in `src/kinetiek/figures/`, named
  `fig_<id>_<slug>()`, returning `alt.Chart`. Pure: no I/O beyond
  `load_curated`.
- Every figure carries `source`, `note`, and `as_of` in its subtitle.
- Registered in `FIGURES: dict[str, Callable]`; essays and pages resolve by ID.
- Save a 2x PNG to `build/figures/<id>.png` at build time. Do not open or
  describe it.

## Maps
Pre-simplified GeoParquet, rendered by pydeck, never full-precision OSM.
Same scale bar on any side-by-side isochrones.
