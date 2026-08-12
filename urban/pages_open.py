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

import pandas as pd
import streamlit as st

from . import chrome
from . import cities
from . import compare
from .theme import SERIES
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

    st.write("")
    st.divider()

    # ---- the ledger: the argument as one figure ----------------------
    figure(
        "01",
        "Every square kilometre each city has, and what happens to it",
        "Both cities run through the same ledger, from the municipal boundary down to land "
        "that may actually be built on.",
        reads_as="Read each column top to bottom. The rows remove land in order, and the last "
                 "two rows are the finding: what is physically left, and what the law allows. "
                 "For Cape Town those two numbers are the same. For Enschede they are 65 and "
                 "zero.",
    )
    compare.ledger_pair()
    provenance(
        "derived",
        "Cape Town: City of Cape Town open data and the biodiversity network. Enschede: "
        "municipal area and built-up area from the constraint sections; the land-use split "
        "between farmland, nature and infrastructure is an estimate.")

    st.write("")
    note(
        "This is the whole report in one figure, and it is why the two cities are worth "
        "putting in the same document. A ledger that stopped one row earlier — at land "
        "physically left — would score Enschede as the healthier of the two, with 65 km² in "
        "hand against Cape Town's 251 km² for a population thirty times larger. Add the last "
        "row and the ranking inverts. Enschede's number is not small. It is zero."
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
    df = compare.scorecard_frame()
    en, ct = df.iloc[0], df.iloc[1]
    note(
        f"The runway figures deserve a caveat that the table cannot carry. Cape Town's "
        f"{ct['Years of growth left']:.0f} years assumes it keeps building at today's density "
        f"of {ct['Density per built km²']:,.0f} people per built square kilometre — already "
        f"higher than Enschede's {en['Density per built km²']:,.0f} — and that every one of "
        f"the remaining 251 km² is usable, which it is not: much of it is steep, sandy, "
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
            "brutal — 251 km² is all there is — but legible. You can price it, trade it, "
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
         "Question": "Which land gets developed, what it is worth, and what the constraint "
                     "costs in hectares.",
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
