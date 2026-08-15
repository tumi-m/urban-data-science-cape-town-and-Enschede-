"""Presentation tokens and the shared Altair configuration.

Lifted out of the app module so the charting helpers can use the same palette
without importing the app, and so there is one definition of each colour rather
than two that drift.

The three categorical slots are the first three of a validated eight-slot
order — the three that clear the colour-vision separation floor on the
all-pairs test, which is the pairlist that applies to scatter and small
multiples. A fourth identity is never generated; where a fourth thing must be
shown it is shown by position or by facet.
"""

from __future__ import annotations

import altair as alt

SURFACE = "#fcfcfb"
SURFACE_2 = "#f4f3f0"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#78766f"
RULE = "#e2e0da"
GRID = "#eceae4"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]

# The highlighted entity in a lens chart: always the first categorical slot.
HIGHLIGHT = SERIES[0]

# Sequential ramp for the maps: one hue, light to dark. Never a rainbow.
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

# Diverging pair for uplift and difference maps: warm and cool poles that read
# as opposite, with a neutral grey midpoint that reads as "nothing".
DIVERGING = ["#184f95", "#3987e5", "#9ec5f4", "#f0efec", "#f6b79b", "#eb6834", "#a83c17"]

# Both rastered geometry figures are square. They render at a fixed pixel size
# rather than stretching to the container: an ellipse would be a lie in a figure
# whose entire content is geometry.
SHED_PX = 400

FONT = (
    "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
)


def style(chart: alt.Chart) -> alt.Chart:
    """Subtract the chrome once, so no chart restates it.

    Everything switched off here is ink that is not data: domain lines, tick
    marks, view frames and legend boxes. What survives is a hairline grid on the
    measured axis, because a reader estimating a value off a log scale needs
    something and estimating from nothing is worse than a faint line.
    """
    return (
        chart.configure_view(stroke=None)
        .configure_axis(
            labelFont=FONT, labelFontSize=11, labelColor=INK_3,
            titleFont=FONT, titleFontSize=11, titleColor=INK_3, titleFontWeight="normal",
            domain=False, ticks=False, grid=False, labelPadding=6, titlePadding=10,
        )
        .configure_axisY(grid=True, gridColor=GRID, gridWidth=1)
        .configure_legend(
            orient="top", title=None, labelFont=FONT, labelFontSize=11, labelColor=INK_2,
            symbolType="square", symbolSize=64, symbolStrokeWidth=0,
            padding=0, columnPadding=14,
        )
        .configure_header(labelFont=FONT, labelFontSize=11, labelColor=INK, titleColor=INK_3)
        .configure_title(anchor="start", font=FONT, fontSize=12, color=INK_2)
        .properties(background=SURFACE)
    )
