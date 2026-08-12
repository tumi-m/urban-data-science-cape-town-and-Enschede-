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


def caveat(title: str, body: str, level: str = "note") -> None:
    """An editorial caveat, styled as editorial rather than as a system fault.

    This replaces `st.error` and `st.warning`, which were being used to carry
    methodological notes. Those components are Streamlit's way of saying the
    program has gone wrong: a red panel headed "Read these numbers correctly"
    is indistinguishable, at a glance, from a stack trace, and the first thing
    a reader asked was that the errors on the simulation pages be fixed. There
    were no errors. There was a red box.

    The information is unchanged and none of it is softened — a caveat that
    matters is still the loudest thing on the page in the ways that count, with
    a coloured rule, a label and full-strength text. What it no longer does is
    impersonate a crash.

    `level` is one of: note (neutral), caution (this limits what you may
    conclude), critical (this invalidates the obvious reading).
    """
    st.markdown(
        f"<div class='caveat {level}'><div class='caveat-label'>{title}</div>"
        f"<div class='caveat-body'>{body}</div></div>",
        unsafe_allow_html=True,
    )


def data_badge(series) -> None:
    """Provenance for a modelled series, stated where it is used.

    Synthetic and reconstructed series get a caveat block rather than a plain
    caption, because a quiet grey footnote is exactly the treatment that lets a
    reader carry a fabricated number out of the room. Everything solid enough
    to stand on gets the one-line caption.
    """
    if series.klass == "synthetic":
        caveat(f"{BADGE[series.klass]} · {series.name}",
               f"{series.source}. {CLASS_NOTE[series.klass]}", "critical")
    elif series.klass == "reconstructed":
        caveat(f"{BADGE[series.klass]} · {series.name}",
               f"{series.source}. {CLASS_NOTE[series.klass]}", "caution")
    else:
        st.caption(series.caption())
