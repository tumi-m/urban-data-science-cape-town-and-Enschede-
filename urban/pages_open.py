"""The opening: the argument, and the two cities in one frame.

This replaces a landing page that stated a thesis about two cities and then
showed one of them. The order here is deliberate and is the order a reader
needs rather than the order the work happened in:

  1. The claim, in one sentence.
  2. The arithmetic that supports it — both cities through one ledger.
  3. The scorecard, so every number that exists for both is shown for both.
  4. What the rest of the report does, and where to go for what.

Nothing on this page is new analysis. It is the same numbers the later sections
compute, assembled so that the comparison happens on the page rather than in
the reader's memory.
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from . import animate
from . import chrome
from . import cities
from . import compare
from . import llm
from .theme import GRID, INK_2, INK_3, SERIES, SURFACE, style
from .ui import figure, header, note, provenance, stats


def page_opening() -> None:
    chrome.hero(
        "Cape Town · Enschede",
        "Two cities that cannot build, for opposite reasons",
        "Cape Town has run out of land. Enschede has land and cannot get permission to use "
        "it. Both are short of housing, both have exhausted the easy answers, and the "
        "measure that would tell you which is in more trouble is the same measure for both. "
        "This report computes it.",
    )

    st.markdown(
        "<div class='answer'>The constraint that binds a city is not always a shortage of "
        "the thing it appears to be short of. Cape Town's limit is a polygon you can draw on "
        "a map. Enschede's is a scalar field you cannot see, cannot draw, and cannot buy your "
        "way past — and it is the more absolute of the two.</div>",
        unsafe_allow_html=True)

    # ---- the divergence, before any numbers -------------------------
    # A thesis stated in words and then proved in tables asks the reader to
    # hold the claim in memory while scrolling for the evidence. This is the
    # claim made visible first: two population curves that share a starting
    # point and almost nothing else, animated so the separation is something
    # the reader watches happen rather than has to imagine.
    _opening_divergence()

    # ---- the four numbers, before anything else ----------------------
    # An opening that states a thesis and then makes the reader scroll for the
    # evidence is asking for trust it has not earned yet. These four are the
    # whole argument, computed from the same series the later sections use.
    df = compare.scorecard_frame()
    en = df[df["City"] == "Enschede"].iloc[0]
    ct = df[df["City"] == "Cape Town"].iloc[0]
    stats([
        ("Cape Town may build on", f"{ct['Land permitted, km²']:,.0f} km²",
         f"Out of {ct['Municipal area, km²']:,.0f} km² of municipality — "
         f"{ct['Land permitted, km²'] / ct['Municipal area, km²']:.0%} of the city."),
        ("Enschede may build on", f"{en['Land permitted, km²']:,.0f} km²",
         f"It has {en['Land physically left, km²']:,.0f} km² of land left and permission "
         f"for none of it."),
        ("Cape Town's runway", f"{ct['Years of growth left']:,.0f} years",
         "Before the land it may build on is gone, at the rate it has grown for a decade."),
        ("Enschede's runway", "0 years",
         "For as long as the nitrogen ruling stands. Density does not help: the test is "
         "categorical."),
    ])

    # The four numbers above are the argument, but a row of stat tiles does
    # not show *how far apart* the two cities are. This is the same ledger as
    # a paired bar chart on a log scale, so the eye takes in three orders of
    # magnitude at once and sees the one bar that drops to zero.
    _opening_land(df)

    st.write("")
    st.divider()

    # ---- the ledger: the argument as one figure ----------------------
    figure(
        "Every square kilometre each city has, and what happens to it",
        "Both cities run through the same ledger, from the municipal boundary down to land "
        "that may actually be built on.",
        reads_as="Read each column top to bottom. The rows remove land in order, and the last "
                 "two rows are the finding: what is physically left, and what the law allows. "
                 f"For Cape Town those two numbers are the same. For Enschede they are "
                 f"{en['Land physically left, km²']:,.0f} and zero.",
    )
    compare.ledger_pair()
    provenance(
        "derived",
        "Cape Town: City of Cape Town open data and the biodiversity network. Enschede: "
        "municipal area and built-up area from the constraint sections; the land-use split "
        "between farmland, nature and infrastructure is an estimate.")

    st.write("")
    note(
        f"This is the whole report in one figure, and it is why the two cities are worth "
        f"putting in the same document. A ledger that stopped one row earlier — at land "
        f"physically left — would score Enschede as the healthier of the two, with "
        f"{en['Land physically left, km²']:,.0f} km² in hand against Cape Town's "
        f"{ct['Land physically left, km²']:,.0f} km² for a population "
        f"{ct['Population'] / en['Population']:.0f} times larger. Add the last row and the "
        f"ranking inverts. Enschede's number is not small. It is zero."
    )

    st.divider()

    # ---- the scorecard ----------------------------------------------
    st.subheader("The same measures, for both")
    note(
        "Every figure below is computed from the series in the later sections rather than "
        "transcribed, so it moves when they do. The highlighted row is the one worth carrying "
        "away: how long the land each city may build on lasts, at the rate it has actually "
        "been growing for the last decade, at its own current density."
    )
    compare.scorecard()
    provenance("derived",
               "Population series, land ledgers and built-up areas from the sections that "
               "follow. Growth rate is the last ten years of each city's own series.")

    st.write("")
    note(
        f"The runway figures deserve a caveat that the table cannot carry. Cape Town's "
        f"{ct['Years of growth left']:.0f} years assumes it keeps building at today's density "
        f"of {ct['Density per built km²']:,.0f} people per built square kilometre — already "
        f"higher than Enschede's {en['Density per built km²']:,.0f} — and that every one of "
        f"the remaining {ct['Land permitted, km²']:,.0f} km² is usable, which it is not: "
        f"much of it is steep, sandy, "
        f"or over the aquifer. The true figure is shorter. Enschede's is zero years for as "
        f"long as the nitrogen ruling stands, and no amount of density changes it, because "
        f"the test is categorical rather than quantitative."
    )

    st.divider()

    # ---- the taxonomy -----------------------------------------------
    st.subheader("Why the two limits behave differently")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chrome.city_card(
            "Cape Town · a polygon",
            "You can draw it, so you can plan around it",
            "A protected area has an edge. Land on one side is available and land on the "
            "other is not, and everyone can see which is which. That makes the constraint "
            f"brutal — {ct['Land permitted, km²']:,.0f} km² is all there is — but legible. "
            "You can price it, trade it, "
            "densify inside it, and argue about moving the line. Every one of those is a "
            "normal planning activity.",
            SERIES[1])
    with c2:
        chrome.city_card(
            "Enschede · a field",
            "You cannot draw it, so you cannot plan around it",
            "Nitrogen deposition has a value everywhere and an edge nowhere. It is produced "
            "somewhere else, mostly by farming, and it lands on a bog that is already four "
            "times over its limit. A project does not fail because of where it is; it fails "
            "because a calculated contribution does not round to zero. There is no line to "
            "move and no site that is safe.",
            SERIES[0])

    st.write("")
    note(
        "This distinction — polygon against field — is the one idea in this report that "
        "transfers to cities that are neither of these. Most planning systems are built to "
        "handle polygons: zoning, edges, overlays, buffers. Field constraints are arriving "
        "everywhere, in the form of air quality, noise, water and carbon budgets, and they "
        "break the machinery, because a categorical test on a continuous quantity cannot be "
        "zoned around. Enschede is not an unlucky Dutch city. It is an early one."
    )

    st.divider()

    # ---- what follows ------------------------------------------------
    st.subheader("What the rest of this does")
    guide = pd.DataFrame([
        {"Section": "2 · How much room is left",
         "Question": "How much land does each city actually have, and what took the rest?",
         "Cities": "Both"},
        {"Section": "3 · Anatomy of a field constraint",
         "Question": "What a limit with no edge does to a city — nitrogen, noise, energy, "
                     "access and a national border, in detail.",
         "Cities": "Enschede"},
        {"Section": "4 · People and growth",
         "Question": "How many people are coming, and how much do the models disagree?",
         "Cities": "Both"},
        {"Section": "5 · Where building goes",
         "Question": "Which land gets developed, what it is worth, and where the constraint "
                     "pushes it.",
         "Cities": "Both"},
        {"Section": "6 · How people travel",
         "Question": "What households choose when prices change, and what that does to the "
                     "nitrogen account.",
         "Cities": "Both"},
        {"Section": "7 · Workbench",
         "Question": "Set two futures against each other and read the difference.",
         "Cities": "Both"},
        {"Section": "8 · Sources",
         "Question": "Every number, where it came from, and what this gets wrong.",
         "Cities": "Both"},
    ])
    st.dataframe(guide, hide_index=True, width="stretch")
    note(
        "Section 3 is the one place the two cities are not treated alike, and the reason is "
        "worth stating plainly rather than hiding: a field constraint takes five sections to "
        "explain because it behaves in ways a reader has no intuition for. Cape Town's limit "
        "takes one section because a reader already understands a fence. That asymmetry is "
        "about the constraints, not about which city got more attention — everything from "
        "section 4 onward runs identically on both."
    )

    # ---- the grounded assistant -------------------------------------
    # The opening states the whole argument; a reader who wants to interrogate
    # it in plain language can. The box is hidden entirely when no key is set,
    # and the model answers only from the numbers computed above.
    context = _opening_context(en, ct)
    llm.assistant_box(context, key="open_llm", label="Ask this overview")


def _opening_context(en, ct) -> str:
    """The opening page's numbers and claims, as one text block for the LLM.

    Only what the page already computed and stated — the LLM may restate this
    but cannot add to it. Provenance classes are kept so a quoted figure carries
    the same caveat it does on the page.
    """
    return f"""This is the opening overview of a report comparing Cape Town and
Enschede, two cities that cannot build for opposite reasons.

THE CLAIM: Cape Town's binding constraint is a polygon you can draw on a map
(protected nature, the urban edge). Enschede's is a scalar field you cannot
draw — nitrogen deposition — and it is the more absolute of the two. A
polygon you can plan around; a field you can only bring down.

POPULATION (indexed to 100 in 1950):
- Cape Town: ends near 780 (almost 8x its 1950 size). Current population
  {ct['Population']:,.0f}; {ct['Growth since 1950']:+.0%} since 1950.
- Enschede: ends near 155, after a thirty-year plateau. Current population
  {en['Population']:,.0f}; {en['Growth since 1950']:+.0%} since 1950.

LAND LEDGER (km²):
- Cape Town: municipal area {ct['Municipal area, km²']:,.0f}; already built on
  {ct['Built-up, km²']:,.0f}; physically left {ct['Land physically left, km²']:,.0f};
  permitted to build on {ct['Land permitted, km²']:,.0f} (same as physical —
  the limit is the polygon, not a separate rule). [derived, City of Cape Town]
- Enschede: municipal area {en['Municipal area, km²']:,.0f}; already built on
  {en['Built-up, km²']:,.0f}; physically left {en['Land physically left, km²']:,.0f};
  permitted to build on {en['Land permitted, km²']:,.0f} (ZERO — the nitrogen
  ruling makes the test categorical). [derived]

RUNWAY (years of growth left at the last decade's rate, at current density):
- Cape Town: {ct['Years of growth left']:.0f} years (shorter in reality — much
  of the permitted land is steep, sandy, or over the aquifer).
- Enschede: 0 years, for as long as the nitrogen ruling stands. Density does
  not help because the test is categorical, not quantitative.

DENSITY (people per built km²): Cape Town {ct['Density per built km²']:,.0f},
Enschede {en['Density per built km²']:,.0f}.

THE TAXONOMY: polygon constraints (zoning, edges, buffers) are legible and
plannable; field constraints (air quality, noise, nitrogen, carbon) arrive
everywhere and break the polygon-based planning machinery because a categorical
test on a continuous quantity cannot be zoned around. Enschede is an early
example of a problem every city is starting to face.
"""


# ---------------------------------------------------------------------
# The two opening visuals
# ---------------------------------------------------------------------
#
# Both are built from series the later sections compute, so the landing page
# is a preview of the report rather than a separate statement of it. Nothing
# here introduces a new number; it shows the ones the page already states.

def _opening_divergence() -> None:
    """The animated population comparison, indexed to 1950 = 100.

    Both cities start at 100 because the point is growth *rates*, not sizes —
    Cape Town has added more people since 1950 than Enschede has ever had, so
    an absolute axis would pin Enschede to the floor. Indexed, the two curves
    separate by a factor of five, and the animation lets a reader watch that
    happen rather than arrive to find it already drawn.
    """
    rows = []
    for c in cities.CITIES.values():
        f, _ = c.population()
        base = float(f["population"].iloc[0])
        rows.append(pd.DataFrame({
            "year": f["year"], "entity": c.name, "index": f["population"] / base * 100,
        }))
    both = pd.concat(rows, ignore_index=True)
    shared = sorted(set(both[both["entity"] == "Enschede"]["year"])
                    & set(both[both["entity"] == "Cape Town"]["year"]))
    palette = {c.name: c.accent for c in cities.CITIES.values()}

    figure(
        "Two cities, one starting point, seventy-four years",
        "Both indexed to 100 in 1950. Press play to watch them separate.",
        reads_as="Cape Town ends near 780 — almost eight times its 1950 size. Enschede ends "
                 "near 155, after a thirty-year plateau in the middle. The models in section "
                 "four have to fit both shapes, and that is where they start to disagree.")
    animate.player(
        "open_divergence", shared,
        lambda i: st.altair_chart(
            animate.lines_upto(
                both, "year", "index", "entity", shared[i],
                x_title="", y_title="index, 1950 = 100", colours=palette,
                x_domain=(shared[0], shared[-1]),
                y_domain=(90, both["index"].max() * 1.06), height=360),
            width="stretch", key="open_divergence_chart"))
    provenance("derived", "Both population series, rebased to 1950.")


def _opening_land(df: pd.DataFrame) -> None:
    """The land ledger as one paired bar chart, on a log scale.

    Four measures, two cities, one axis: municipal area, what is already built
    on, what is physically left, and what the law permits. Logarithmic because
    the two cities span three orders of magnitude, and because the whole point
    — Enschede's permitted bar collapsing to zero — cannot be drawn on a linear
    scale that also shows Cape Town's 2,451 km². The zero is stated in the
    caption rather than nudged onto the axis, which is the rule this codebase
    keeps for exactly this case.
    """
    rows = []
    for city, row in [("Enschede", df[df["City"] == "Enschede"].iloc[0]),
                      ("Cape Town", df[df["City"] == "Cape Town"].iloc[0])]:
        rows.append({"measure": "Municipal area", "city": city,
                     "km²": float(row["Municipal area, km²"])})
        rows.append({"measure": "Already built on", "city": city,
                     "km²": float(row["Built-up, km²"])})
        rows.append({"measure": "Land physically left", "city": city,
                     "km²": float(row["Land physically left, km²"])})
        rows.append({"measure": "Land it may build on", "city": city,
                     "km²": float(row["Land permitted, km²"])})
    land = pd.DataFrame(rows)
    order = ["Municipal area", "Already built on", "Land physically left",
             "Land it may build on"]
    land["measure"] = pd.Categorical(land["measure"], order, ordered=True)
    palette = {c.name: c.accent for c in cities.CITIES.values()}

    bars = (
        alt.Chart(land)
        .mark_bar(stroke=SURFACE, strokeWidth=1)
        .encode(
            x=alt.X("km²:Q", scale=alt.Scale(type="log", domain=[1, 3000]),
                    axis=alt.Axis(format="~s", grid=True, gridColor=GRID),
                    title="km² (log scale)"),
            y=alt.Y("measure:N", sort=order, title=None,
                    axis=alt.Axis(labelLimit=220, labelFontSize=11)),
            color=alt.Color("city:N", scale=alt.Scale(
                domain=list(palette), range=list(palette.values())),
                legend=alt.Legend(orient="top", title=None)),
            tooltip=["city", "measure", alt.Tooltip("km²:Q", format=",.0f")],
        )
    )
    # Label the non-zero bars with their value; the zero bar is labelled in
    # the caption, never nudged onto a log axis it cannot live on.
    labelled = land[land["km²"] > 0]
    text = (
        alt.Chart(labelled)
        .mark_text(align="left", dx=6, fontSize=10, color=INK_2)
        .encode(x="km²:Q", y=alt.Y("measure:N", sort=order),
                text=alt.Text("km²:Q", format=",.0f"))
    )
    st.altair_chart(style(alt.layer(bars, text).properties(height=260)),
                    width="stretch", key="open_land")
    st.caption(
        "Enschede's “Land it may build on” bar is zero and so cannot appear on a log axis — "
        "that is the finding, stated here rather than drawn as a sliver that would understate "
        "it. Cape Town's permitted land is the same as its physical remainder; Enschede's is "
        "not, which is the whole argument.")
    provenance("derived", "The land ledgers computed in section 2.")
