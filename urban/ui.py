"""Shared layout primitives, so no section invents its own.

Kept deliberately small. The point of a layout vocabulary is that a reader
learns it once — a header looks like a header, provenance sits in the same place
under every figure, a number that is the story is a stat tile rather than a
one-bar bar chart.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .provenance import BADGE, CLASS_NOTE
from .theme import INK_2


def header(index: str, title: str, lede: str) -> None:
    st.caption(index.upper())
    st.title(title)
    st.markdown(
        f"<p style='font-size:1.05rem;line-height:1.65;max-width:62ch'>{lede}</p>",
        unsafe_allow_html=True,
    )
    st.write("")


def stats(items: list[tuple[str, str, str]]) -> None:
    """A row of stat tiles. Used instead of a one-bar bar chart, never beside one."""
    cols = st.columns(len(items))
    for col, (label, value, note_text) in zip(cols, items):
        with col:
            st.metric(label, value)
            st.caption(note_text)


def figure(n: str, title: str, deck: str, reads_as: str | None = None) -> None:
    """A chart heading a reader can use.

    Three lines, each doing one job, in the order a reader needs them:

        CHART 3          where you are
        The title        what is plotted
        How to read it   what to do with it

    The old version ran the title and a long description together in small grey
    text, which meant the description was the same weight as the caption, the
    source line and the axis labels — four kinds of text at one size, none of
    them signalling what it was for. Whatever is left in `deck` should be short.
    `reads_as` is the sentence that tells you what you are looking at.
    """
    st.markdown(
        f"<div class='fig-head'>"
        f"<div class='fig-num'>Chart {n.lstrip('0') or n}</div>"
        f"<div class='fig-title'>{title}</div>"
        f"<div class='fig-deck'>{deck}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if reads_as:
        st.markdown(
            f"<div class='fig-read'><span>How to read it</span>{reads_as}</div>",
            unsafe_allow_html=True,
        )


def provenance(klass: str, sources: str) -> None:
    """Source line under a figure, in words rather than in shorthand."""
    words = {
        "official": "Published figures",
        "derived": "Worked out here",
        "engineering": "Standard engineering values",
        "estimate": "Estimate",
        "reconstructed": "Reconstructed series",
        "synthetic": "Made-up data",
    }
    st.markdown(
        f"<div class='fig-source'>{words.get(klass, klass)} · {sources}</div>",
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    st.markdown(
        f"<p style='font-size:0.85rem;line-height:1.6;color:{INK_2};max-width:68ch'>{text}</p>",
        unsafe_allow_html=True,
    )


def values_table(df: pd.DataFrame) -> None:
    """The accessible reading of any chart, and the required relief wherever a
    series colour sits below three to one against the surface."""
    with st.expander("Values"):
        st.dataframe(df, hide_index=True, width="stretch")


def data_badge(series) -> None:
    """Provenance for a modelled series, stated where it is used.

    Deliberately an `st.warning` rather than a caption when the underlying data
    is synthetic. A quiet grey footnote is exactly the treatment that lets a
    reader carry a fabricated number out of the room.
    """
    if series.klass == "synthetic":
        st.warning(f"{BADGE[series.klass]} — {series.source}. {CLASS_NOTE[series.klass]}")
    elif series.klass == "reconstructed":
        st.info(f"{BADGE[series.klass]} — {series.source}. {CLASS_NOTE[series.klass]}")
    else:
        st.caption(series.caption())
