# Cape Town and Enschede — what limits building

Two cities that are hard to build in for opposite reasons.

**Cape Town has run out of land.** Mountain on one side, ocean on two, about a third of
what is left protected. What remains is a flat sandy plain that is both expensive to
build on and the roof of the city's emergency water supply.

**Enschede has plenty of land and still cannot build.** 140 km² for 161,000 people, only
43 km² of it built on. What stops it is not land at all — it is nitrogen in the air,
noise at the window, risk near a pipeline, travel time to a well.

That difference is the point of putting them in one project:

> **Some limits are lines on a map. Others are measurements. You can only argue about a
> line, but you can actually bring a measurement down — and bringing it down frees up
> every location at once.**

## What the analysis concludes

| Section | Finding |
|---|---|
| **Cape Town** | 895 km² buildable out of 2,451 km² of city, for 4.8 million people. The urban edge and protected nature push housing onto the Cape Flats — loose sand that is expensive to build tall on, directly above the aquifer the city fell back on in the drought. Every decision is reasonable alone; together they trap the city. |
| **Both cities** | The limit pushes building to the worst available place in both. The tool draws maps, so the answer always comes back as a map — even though Cape Town's real problem is that the trains stopped and Enschede's is a chemical measurement. In both, the cheapest fix is not construction. |
| **Constraints** | Five of Enschede's seven principal limits are fields with a source, a decay and a lever. Two are genuine polygons — and those two dominate public argument about growth. |
| **Nitrogen** | Since the 2019 annulment of the programmatic approach there is no de minimis increase: the test is whether a project rounds to zero. Over a fifty-year life, ~92% of a dwelling's nitrogen oxides come from the traffic it attracts, not the plant that builds it. Location and parking norms *are* emissions instruments. |
| **Mobility** | The energy ladder spans a factor of ~46 from petrol car to electric bicycle in passenger-kilometres per kilowatt-hour. Enschede sits on an ice-pushed ridge, so a 30 m climb costs a rider ~31 Wh of food energy and a motor ~9 Wh — under a kilometre of e-bike range. Assistance removes a barrier that, uniquely in the Netherlands, actually exists here. |
| **Access** | The station buffer radius is a policy variable, not a property of the rail network, and shed area goes as r²: the same station has 14× the catchment at a cycling radius. Enschede's three stations reach 8% of built-up land on foot and 82% of *residents* by bicycle, with nothing built. Land is also the wrong denominator — counted in people rather than hectares, coverage runs a fifth higher at the walking radius. |
| **Border** | The national border removes ~37% of a 20 km catchment and ~42% of a 30 km one, by geometry alone. The loss grows with radius, so it takes away regional functions while local ones look healthy. Permeability — an institutional quantity — moves more accessible population than anything that could be built. |
| **Energy** | Per unit of energy, ground-mounted solar withdraws ~84× the land onshore wind does. Wind is blocked by fields (noise, flicker, radar, habitat); solar is blocked by a polygon. A search-area process therefore converges on the land-hungry option because its obstacle is the negotiable kind. |
| **Population** | The curve is three regimes, not one: textile-era growth, a thirty-year plateau, then slow renewed growth. Natural increase went to roughly zero decades ago and domestic migration is persistently negative — what holds the total up is international migration alone. Gross and built-up density diverge, which is what sprawl looks like in a chart. |
| **Projection** | Seven model families on identical data disagree about 2050 by ~24,600 people, about 15% of the city. The two with the *best* backtest scores are the two that cannot extrapolate at all. The section's finding is that the functional form decides the answer, and the functional form is an assumption. |
| **Development** | A classifier over accessibility, density and the constraint mask, plus a hedonic value surface. Trained on synthetic labels — so a good score measures whether the learner recovers assumptions put there on purpose, which the page states in red rather than in a footnote. |
| **Simulation** | A constrained cellular automaton (SLEUTH / UrbanSim lineage) allocating projected growth year by year. Only one output is defended: the *difference* between two runs that differ in one assumption, where the synthetic inputs cancel. |

## Provenance discipline

Every number rendered anywhere carries a **class** and a **source**, and the class
travels with the figure rather than sitting in a footnote:

- `official` — published by a named authority, reproducible by opening their document
- `derived` — computed here from stated inputs, with the arithmetic given alongside
- `engineering` — a standard physics or engineering parameter, quoted with its range
- `estimate` — an order-of-magnitude figure held in place until the authoritative layer
  is wired in

The modelling layer adds two more, because its failure mode is different in kind. A
chart of an estimate is roughly right; a *model* fitted to a weak series produces a
forecast, an R², a confidence band and a map that all look exactly like the output of a
model fitted to real data. The apparatus manufactures credibility whether or not the
inputs deserve it, so the inputs announce themselves at every point of use:

- `reconstructed` — a real series written down from knowledge rather than pulled from
  the source. Right in shape and magnitude, wrong in the third digit
- `synthetic` — generated here by a stated process. **Not data about Enschede.** Present
  so the machinery can be built and tested end to end

`worst_class()` enforces the rule that a result inherits the class of its weakest input —
combining an official series with a synthetic one does not yield something half-official.
Synthetic inputs surface as a red banner in the UI, never as a grey caption.

**On data availability.** `urban/demography.py` contains a real StatLine fetch path. Where
the host has outbound access it uses the live series and labels it `official`; where it
does not, it falls back to the reconstructed series and says so on every chart drawn from
it. Which one is in play is always visible.

Where a conclusion rests on an `estimate`, it is written to survive that figure's
replacement, or it is not drawn. Sources are listed in full at `/methods`, together with
the analysis's known weaknesses.

**Nothing here is a permit assessment.** No dispersion model is run: the nitrogen
section works entirely on the emission side, because a plausible-looking imitation of the
official calculator would be more dangerous than an obvious gap. No figure on this site
should be carried into an environmental impact assessment, an acoustic report or a siting
study.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js (App Router), React 19 | Pages are server-rendered; only the interactive figures ship as client components |
| Styling | Tailwind CSS v4 | Utility-first, used to enforce a tight typographic scale and a high data-ink ratio rather than to decorate |
| Declarative charts | Vega-Lite via `vega-embed` | Anything with a standard form — dot plots, bars, dumbbells, lines |
| Bespoke figures | D3 (`d3-scale`, `d3-shape`, `d3-selection`, `d3-array`) | The four figures that are geometry rather than charts: constraint shapes, the cut catchment disc, the ridge transect, the station access sheds |
| Types | TypeScript, strict | Every quantity is a typed value with a unit, a class and a source |
| ML / stats | scikit-learn, SciPy | Model registry, backtesting, development classifier, growth-curve fitting |
| Maps | pydeck (deck.gl) over CartoDB Positron raster tiles | Real coordinates and real catchment radii, with no API key or account needed; label-free `light_nolabels` style |
| Streamlit app | Streamlit + Altair | Python port of the platform, plus the interactive modelling sections |

### Chart rules the codebase enforces

Chrome is subtracted once, in `lib/vegaTheme.ts`, so no chart restates it: no domain
lines, no tick marks, no view frames, no legend boxes, one hairline grid on the measured
axis only. Beyond that:

- No dual-axis charts, anywhere.
- Quantities spanning orders of magnitude are plotted logarithmically; where the log axis
  makes values unreadable, every point is labelled — the one case where labelling
  everything is right rather than careless.
- A zero that cannot be drawn on a log scale is stated in the caption, never nudged onto
  the scale.
- Touching fills are separated by a 2 px gap in the surface colour, not by a stroke.
- Text wears text tokens; the coloured mark beside it carries identity.
- The categorical palette is three slots from a validated eight-slot order — the three
  that clear the colour-vision separation floor on the all-pairs test in both modes.
  Charts whose series colour falls below 3:1 against the surface carry a values table.
- Dark mode is a second set of steps chosen against the dark surface, not an inversion.

## Running it

```bash
npm install
npm run dev        # http://localhost:3000
```

```bash
npm run build && npm start   # production
npm run typecheck            # tsc --noEmit
```

## Layout

```
app/                    routes — one per analytical section, plus /methods
components/
  charts/               Vega-Lite chart components (client)
  d3/                   bespoke figures: ConstraintShapes, CatchmentGeometry, RidgeProfile, AccessSheds
  VegaChart.tsx         embed wrapper — re-renders on colour-scheme change
  Figure.tsx            figure frame, stat tile, prose measure
data/                   typed analytical modules; every figure is a value + unit + class + source
lib/
  provenance.ts         the Quantity/Source types and the source registry
  vegaTheme.ts          shared chart configuration, read from live CSS custom properties

streamlit_app.py        Streamlit entry point — constraint sections, ported to Altair
urban/                  the modelling layer
  provenance.py         the two extra classes, and the weakest-input rule
  demography.py         population, density, flows; live fetch with a labelled fallback
  forecast.py           model registry, tail backtesting, projection to 2050
  spatial.py            development classifier, hedonic surface, growth simulation
  owid.py               chart forms in the Our World in Data idiom
  geo.py                real coordinates and OpenStreetMap maps
  capetown.py           Cape Town figures, portal fetch path, and further analysis
  sources.py            ArcGIS feature-service client for Cape Town open data
  cct_catalog.py        derived figures from real Cape Town layers; evidence table
  lens.py               Evans/Dediu chart kit: trajectory, crossing_time, share_vs_growth
  theme.py / ui.py      tokens and layout primitives shared with the app
```

## Two deployments, one analysis

**The Streamlit app is the deployed one.** It carries the whole analysis — both
cities, all the constraint sections, and the four modelling sections that need
widgets and compute. The Next.js platform is the same argument as a static essay.

```bash
streamlit run streamlit_app.py     # or point Streamlit Cloud at this file
```

## Reproducibility

The Python environment is pinned in `repro_lock.txt` — install with
`pip install -r repro_lock.txt` to reproduce the exact verified stack.
The Streamlit app caches layer fetches (`st.cache_data` on `_cct_catalog`)
so re-renders do not re-hit the Cape Town open data portal.

The sidebar has two controls rather than one long list. The first picks what you
want to look at — **Overview (both cities)**, **Enschede**, **Cape Town**, or
**Data and models** — and the second picks the section within it. Fourteen items in
a flat list is a wall, and it hides the fact that the two cities are analysed to
very different depths.

The port duplicates the analytical constants in Python — Streamlit Cloud cannot read the
TypeScript modules — and that duplication is a real cost. Everything that could drift lives
in one marked `CONSTANTS` block at the top of `streamlit_app.py`, in the same order as the
`data/*.ts` modules it mirrors.

The data modules are the analysis. `app/` renders them and adds argument; it does not
compute anything the modules do not expose.

## Extending it

The natural next step is to replace the `estimate`-class figures with the real layers —
building footprints and the elevation model for rooftop potential, a habitat-hexagon pull
for deposition, a real border geometry and population surface for the catchment model.
Each of those is an open service. The typed modules are shaped so that swapping a value
changes the figure and nothing else, and every conclusion has been written to hold when
that happens.
