"""Visual chrome for the Streamlit app.

Streamlit's defaults are built to make any script presentable, which means they
are loud enough to survive a bad one: heavy metric numerals, wide gaps, dividers
at full contrast, form controls sized for touch. On a page that is mostly
reading and charts, all of that competes with the content.

This module turns the volume down. It is one stylesheet plus a hero block, and
everything in it is subtraction: lighter rules, tighter vertical rhythm, quieter
captions, metrics that read as a row of facts rather than a dashboard.

Colours come from `theme.py` so there is one palette, not two.
"""

from __future__ import annotations

import streamlit as st

from .theme import GRID, INK, INK_2, INK_3, RULE, SERIES, SURFACE, SURFACE_2

CSS = f"""
<style>
  /* ---------- page rhythm ---------- */
  .block-container {{
      padding-top: 2.6rem;
      padding-bottom: 5rem;
      max-width: 1180px;
  }}

  /* ---------- type ---------- */
  html, body, [class*="css"] {{
      font-feature-settings: "tnum" 1;
  }}
  h1 {{
      font-weight: 650 !important;
      letter-spacing: -0.021em !important;
      line-height: 1.14 !important;
      margin-bottom: 0.45rem !important;
  }}
  h2 {{
      font-weight: 600 !important;
      letter-spacing: -0.012em !important;
      font-size: 1.32rem !important;
      margin-top: 0.4rem !important;
      padding-top: 0.75rem;
      border-top: 1px solid {RULE};
  }}
  h3 {{
      font-weight: 550 !important;
      font-size: 1.02rem !important;
  }}
  p, li {{ color: {INK_2}; }}

  /* ---------- dividers: hairline, not a bar ---------- */
  hr {{
      margin: 2.1rem 0 1.5rem 0 !important;
      border-color: {RULE} !important;
      opacity: 1;
  }}

  /* ---------- metrics as a row of facts ---------- */
  [data-testid="stMetric"] {{
      border-top: 1px solid {RULE};
      padding: 0.7rem 0 0 0;
  }}
  [data-testid="stMetricLabel"] p {{
      font-size: 0.68rem !important;
      text-transform: uppercase;
      letter-spacing: 0.09em;
      color: {INK_3} !important;
      font-weight: 500 !important;
  }}
  [data-testid="stMetricValue"] {{
      font-size: 1.95rem !important;
      font-weight: 600 !important;
      letter-spacing: -0.02em;
      color: {INK} !important;
      line-height: 1.1 !important;
  }}
  [data-testid="stCaptionContainer"] p {{
      color: {INK_3} !important;
      font-size: 0.75rem !important;
      line-height: 1.5 !important;
  }}

  /* ---------- sidebar ---------- */
  [data-testid="stSidebar"] {{
      background: {SURFACE_2};
      border-right: 1px solid {RULE};
  }}
  [data-testid="stSidebar"] .block-container {{ padding-top: 1.6rem; }}
  [data-testid="stSidebarNav"] a span {{ font-size: 0.86rem; }}

  /* ---------- controls, quietened ---------- */
  [data-testid="stExpander"] details {{
      border: 1px solid {RULE};
      border-radius: 6px;
      background: transparent;
  }}
  [data-testid="stExpander"] summary p {{ font-size: 0.84rem; }}
  .stSlider label p, .stSelectbox label p, .stRadio label p, .stCheckbox label p {{
      font-size: 0.78rem !important;
      color: {INK_3} !important;
  }}

  /* ---------- tables ---------- */
  [data-testid="stDataFrame"] {{ border: 1px solid {RULE}; border-radius: 6px; }}

  /* ---------- callouts: keep the red loud, soften the rest ---------- */
  [data-testid="stAlert"] {{ border-radius: 6px; font-size: 0.85rem; }}

  /* ---------- figure headings ----------
     Three sizes doing three jobs. Before this, the number, the title, the
     description, the source line and the axis labels were all the same small
     grey text, so nothing told a reader which was which. */
  .fig-head {{ margin: 0.2rem 0 0.55rem 0; }}
  .fig-num {{
      font-size: 0.66rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: {SERIES[0]};
      font-weight: 600;
      margin-bottom: 0.2rem;
  }}
  .fig-title {{
      font-size: 1.06rem;
      font-weight: 600;
      color: {INK};
      line-height: 1.3;
      letter-spacing: -0.01em;
      margin-bottom: 0.28rem;
  }}
  .fig-deck {{
      font-size: 0.86rem;
      line-height: 1.55;
      color: {INK_2};
      max-width: 78ch;
  }}
  .fig-read {{
      border-left: 2px solid {SERIES[1]};
      padding: 0.15rem 0 0.15rem 0.85rem;
      margin: 0.9rem 0 0.3rem 0;
      font-size: 0.88rem;
      line-height: 1.6;
      color: {INK};
      max-width: 78ch;
  }}
  .fig-read span {{
      display: block;
      font-size: 0.64rem;
      text-transform: uppercase;
      letter-spacing: 0.11em;
      color: {INK_3};
      margin-bottom: 0.2rem;
      font-weight: 600;
  }}
  .fig-source {{
      font-size: 0.7rem;
      color: {INK_3};
      margin-top: 0.5rem;
      padding-top: 0.4rem;
      border-top: 1px solid {GRID};
      max-width: 78ch;
  }}

  /* ---------- maps and legends ----------
     deck.gl draws no legend of its own, so every map carries one in HTML
     underneath it. The container is given room for the axis/legend band so
     nothing is cropped into a nested scrollbar. */
  .map-wrap {{ margin: 0.2rem 0 0.4rem 0; }}
  .map-note {{
      font-size: 0.72rem;
      color: {INK_3};
      margin-top: 0.35rem;
  }}

  /* Charts must never be clipped by their card. */
  [data-testid="stVegaLiteChart"] {{ overflow: visible !important; }}
  [data-testid="stVegaLiteChart"] > div {{ overflow: visible !important; }}

  /* Legends and axis text large enough to read. */
  .vega-embed .role-legend text {{ font-size: 11px !important; }}

  /* ---------- hero ---------- */
  .hero {{
      border-top: 2px solid {INK};
      padding-top: 1.5rem;
      margin-bottom: 2.4rem;
  }}
  .hero .kicker {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: {INK_3};
      margin-bottom: 0.7rem;
  }}
  .hero h1 {{
      font-size: 2.5rem;
      line-height: 1.1;
      letter-spacing: -0.025em;
      color: {INK};
      margin: 0 0 1rem 0;
  }}
  .hero .standfirst {{
      font-size: 1.06rem;
      line-height: 1.62;
      color: {INK_2};
      max-width: 60ch;
  }}

  /* ---------- two-city cards ---------- */
  .city-card {{
      border-top: 3px solid var(--accent);
      padding: 0.85rem 0 0 0;
      height: 100%;
  }}
  .city-card .city-name {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: {INK_3};
      margin-bottom: 0.35rem;
  }}
  .city-card .city-claim {{
      font-size: 1.02rem;
      font-weight: 550;
      color: {INK};
      line-height: 1.35;
      margin-bottom: 0.4rem;
  }}
  .city-card .city-body {{
      font-size: 0.85rem;
      line-height: 1.6;
      color: {INK_2};
  }}
</style>
"""


def inject() -> None:
    """Apply the stylesheet. Call once, first thing in the app."""
    st.markdown(CSS, unsafe_allow_html=True)


def hero(kicker: str, title: str, standfirst: str) -> None:
    """The landing block. One claim, stated once, above everything else."""
    st.markdown(
        f"""<div class="hero">
              <div class="kicker">{kicker}</div>
              <h1>{title}</h1>
              <div class="standfirst">{standfirst}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def city_card(name: str, claim: str, body: str, accent: str) -> None:
    """One of the two cities, as a card. Used only on the landing page."""
    st.markdown(
        f"""<div class="city-card" style="--accent:{accent}">
              <div class="city-name">{name}</div>
              <div class="city-claim">{claim}</div>
              <div class="city-body">{body}</div>
            </div>""",
        unsafe_allow_html=True,
    )


ACCENT_CT = SERIES[1]
ACCENT_EN = SERIES[0]
