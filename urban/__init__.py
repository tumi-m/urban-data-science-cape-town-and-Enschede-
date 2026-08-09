"""Modelling and charting layer for the Enschede constraint platform.

The visualisation sections of this project are deterministic: geometry, physics
and accounting, all of it checkable by hand. This package is where the
statistical work lives, and it is separated for a reason. A fitted model
produces a forecast, a score, a confidence band and a map whether or not its
inputs deserve any of them, so the code that does the fitting is kept together
with the code that labels its provenance.

    provenance  the two extra classes the modelling layer needs, and the rule
                that a result inherits the class of its weakest input
    demography  population, density and flows, with a live-fetch path and a
                labelled fallback
    forecast    the model registry, backtesting and projection to 2050
    spatial     development classifier, hedonic value surface, and the growth
                simulation
    owid        chart forms in the Our World in Data idiom
    theme       tokens and the shared Altair configuration
    ui          layout primitives shared with the app
"""

from . import demography, forecast, owid, provenance, spatial, theme, ui  # noqa: F401

__all__ = ["demography", "forecast", "owid", "provenance", "spatial", "theme", "ui"]
