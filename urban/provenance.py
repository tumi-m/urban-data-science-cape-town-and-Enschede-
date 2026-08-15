"""Provenance classes for the modelling layer.

The visualisation platform already carries four classes — official, derived,
engineering, estimate. The modelling sections need two more, and they need them
loudly, because the failure mode here is different in kind.

A chart of an estimate is a chart that is roughly right. A *model* fitted to a
series that was reconstructed rather than downloaded will produce a forecast,
an R², a confidence band and a map, all of which look exactly like the output
of a model fitted to real data. The apparatus manufactures credibility whether
or not the inputs deserve it, so the inputs have to announce themselves at
every point of use.

    reconstructed  A real-world series written down from knowledge rather than
                   pulled from the authoritative source. Right in shape and
                   order of magnitude; wrong in the third digit. Conclusions
                   about trend and structure survive; conclusions about a
                   specific year do not.

    synthetic      Generated here by a stated process. It is not data about
                   Enschede at all. It exists so the machinery can be built,
                   demonstrated and tested end to end, and it must be replaced
                   before any output is believed.

Nothing in this package silently upgrades a class. A model trained on
synthetic inputs reports synthetic outputs.
"""

from __future__ import annotations

from dataclasses import dataclass

RECONSTRUCTED = "reconstructed"
SYNTHETIC = "synthetic"
OFFICIAL = "official"
DERIVED = "derived"
ESTIMATE = "estimate"

CLASS_NOTE = {
    OFFICIAL: "Published by a named authority.",
    DERIVED: "Computed here from stated inputs.",
    RECONSTRUCTED: (
        "Written down from knowledge rather than pulled from the source. Right in shape and "
        "magnitude, wrong in the third digit. Use it for trend and structure, not for a year."
    ),
    SYNTHETIC: (
        "Generated here by a stated process. Not data about Enschede. Present so the machinery "
        "can be built and tested end to end; replace before believing any output."
    ),
}

BADGE = {
    OFFICIAL: "🟢 official",
    DERIVED: "🔵 derived",
    RECONSTRUCTED: "🟡 reconstructed",
    SYNTHETIC: "🔴 synthetic",
}


@dataclass(frozen=True)
class Series:
    """A named series that knows how good it is."""

    name: str
    klass: str
    source: str
    note: str = ""

    @property
    def badge(self) -> str:
        return BADGE[self.klass]

    def caption(self) -> str:
        bits = [self.badge, self.source]
        if self.note:
            bits.append(self.note)
        return " · ".join(bits)


def worst_class(*classes: str) -> str:
    """The class of a result is the class of its weakest input.

    Combining an official series with a synthetic one does not yield something
    half-official. This is the rule that stops the modelling layer laundering
    its inputs.
    """
    order = [OFFICIAL, DERIVED, RECONSTRUCTED, SYNTHETIC]
    return max(classes, key=order.index)
