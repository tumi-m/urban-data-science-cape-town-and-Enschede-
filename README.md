# Enschede — spatial constraints

A constraint analysis of Enschede (Twente, Overijssel) built as a data-visualisation
platform, arguing one thing:

> **The limits that bind this city are scalar fields, not boundaries — and a field can be
> lowered, where a boundary can only be moved or fought.**

Enschede is normally described through its edges: a settlement boundary, a nature
network, a national frontier four kilometres from the centre. Those edges are real and
they are not what stops the city building. What stops it is a set of continuous
quantities with thresholds — deposited nitrogen, sound level, fatality probability,
groundwater travel time, radar sightline — that a map can only render as a contour.
Treating a contour as a fence discards the fact that the quantity underneath it can be
reduced, and reducing it relaxes every location at once.

## What the analysis concludes

| Section | Finding |
|---|---|
| **Constraints** | Five of Enschede's seven principal limits are fields with a source, a decay and a lever. Two are genuine polygons — and those two dominate public argument about growth. |
| **Nitrogen** | Since the 2019 annulment of the programmatic approach there is no de minimis increase: the test is whether a project rounds to zero. Over a fifty-year life, ~92% of a dwelling's nitrogen oxides come from the traffic it attracts, not the plant that builds it. Location and parking norms *are* emissions instruments. |
| **Mobility** | The energy ladder spans a factor of ~46 from petrol car to electric bicycle in passenger-kilometres per kilowatt-hour. Enschede sits on an ice-pushed ridge, so a 30 m climb costs a rider ~31 Wh of food energy and a motor ~9 Wh — under a kilometre of e-bike range. Assistance removes a barrier that, uniquely in the Netherlands, actually exists here. |
| **Border** | The national border removes ~37% of a 20 km catchment and ~42% of a 30 km one, by geometry alone. The loss grows with radius, so it takes away regional functions while local ones look healthy. Permeability — an institutional quantity — moves more accessible population than anything that could be built. |
| **Energy** | Per unit of energy, ground-mounted solar withdraws ~84× the land onshore wind does. Wind is blocked by fields (noise, flicker, radar, habitat); solar is blocked by a polygon. A search-area process therefore converges on the land-hungry option because its obstacle is the negotiable kind. |

## Provenance discipline

Every number rendered anywhere carries a **class** and a **source**, and the class
travels with the figure rather than sitting in a footnote:

- `official` — published by a named authority, reproducible by opening their document
- `derived` — computed here from stated inputs, with the arithmetic given alongside
- `engineering` — a standard physics or engineering parameter, quoted with its range
- `estimate` — an order-of-magnitude figure held in place until the authoritative layer
  is wired in

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
| Bespoke figures | D3 (`d3-scale`, `d3-shape`, `d3-selection`, `d3-array`) | The three figures that are geometry rather than charts: constraint shapes, the cut catchment disc, the ridge transect |
| Types | TypeScript, strict | Every quantity is a typed value with a unit, a class and a source |

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
  d3/                   bespoke figures: ConstraintShapes, CatchmentGeometry, RidgeProfile
  VegaChart.tsx         embed wrapper — re-renders on colour-scheme change
  Figure.tsx            figure frame, stat tile, prose measure
data/                   typed analytical modules; every figure is a value + unit + class + source
lib/
  provenance.ts         the Quantity/Source types and the source registry
  vegaTheme.ts          shared chart configuration, read from live CSS custom properties
```

The data modules are the analysis. `app/` renders them and adds argument; it does not
compute anything the modules do not expose.

## Extending it

The natural next step is to replace the `estimate`-class figures with the real layers —
building footprints and the elevation model for rooftop potential, a habitat-hexagon pull
for deposition, a real border geometry and population surface for the catchment model.
Each of those is an open service. The typed modules are shaped so that swapping a value
changes the figure and nothing else, and every conclusion has been written to hold when
that happens.
