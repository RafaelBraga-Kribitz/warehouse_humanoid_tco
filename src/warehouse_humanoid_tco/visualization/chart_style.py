"""Executive-chart roles and formatting helpers on the Braga design system v2.1.

Every colour, face and size comes from ``bk_theme`` (bk-viz >= 2.0.0); this module holds no
colour value of its own. The four constants below are design-system *role names*, resolved in
the current render mode with :func:`color` (``bk.c``):

* ``RECOMMENDED`` — the one highlight per chart (``hl``): the crew the analysis recommends.
* ``BASELINE`` — the legacy reference crew and reference marks (IBCS previous, ``sc-py``).
* ``OTHER`` — every other crew, structure grey (``ink-2``, the base of ``bk.highlight_palette``).
* ``ADVERSE`` — a bad variance (IBCS ``var-neg``); its label carries ▲ (``bk.variance_label``).
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import bk_theme as bk
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, ScalarFormatter

RECOMMENDED = "hl"
BASELINE = "sc-py"
OTHER = "ink-2"
ADVERSE = "var-neg"

#: Smallest type the system allows (12px at the figure's 96 px/in).
SMALL = bk.SIZE["mono-sm"]


def use_theme(mode: str = "light") -> None:
    """Install the design system (fonts, surfaces, hairlines) before any figure is drawn."""
    bk.apply(mode)


def color(role: str) -> str:
    """Resolve a design-system colour role in the current mode."""
    return bk.c(role)


def apply_style(ax: Axes) -> None:
    """Hairline chrome from the design system, without scientific-offset notation."""
    bk.strip_chrome(ax, keep=("left", "bottom"))
    ax.set_axisbelow(True)
    for axis in (ax.xaxis, ax.yaxis):
        formatter = axis.get_major_formatter()
        if isinstance(formatter, ScalarFormatter):
            formatter.set_scientific(False)
            formatter.set_useOffset(False)


_TITLE_TOP: dict[int, float] = {}


def title(ax: Axes, text: str, context: str | None = None) -> None:
    """Chart title in the display face at the figure's left edge; the line under it in ink-2.

    Set at figure level so a long title never runs past the plot when the category labels
    take the left of the canvas. :func:`layout` keeps the axes clear of it.
    """
    fig = cast(Figure, ax.get_figure())
    height_in = float(fig.get_size_inches()[1])
    used_in = 0.18
    fig.text(
        0.02,
        1 - used_in / height_in,
        text,
        ha="left",
        va="top",
        color=bk.c("ink"),
        fontproperties=bk.font("display", "black", "project"),
    )
    used_in += bk.SIZE["project"] * 1.25 / 72
    if context:
        used_in += 0.04
        fig.text(
            0.02,
            1 - used_in / height_in,
            context,
            ha="left",
            va="top",
            color=bk.c("ink-2"),
            fontproperties=bk.font("display", "regular", "body"),
        )
        used_in += bk.SIZE["body"] * 1.3 / 72
    _TITLE_TOP[id(fig)] = 1 - (used_in + 0.12) / height_in


def layout(fig: Figure, bottom: float, right: float = 1.0) -> None:
    """Fit the axes between the figure-level title and the provenance footer.

    ``right`` keeps room for labels written past the plot's right edge, since the figure is
    saved at its explicit size rather than re-cropped.
    """
    fig.tight_layout(rect=(0, bottom, right, _TITLE_TOP.pop(id(fig), 1.0)))


def footer(fig: Figure, source: str, run_id: str | None = None, note: str | None = None) -> None:
    """Provenance strip under the chart: source, run and the epistemic tag of a model output."""
    bk.footer(
        fig,
        source=source,
        run_id=run_id or "",  # bk.footer skips an empty run id and an empty note
        tag="SIMULATED",
        note=note or "",
        left=0.02,
        y=0.045,
    )


def save_png(fig: Figure, path: Path, dpi: int) -> Path:
    """Write the figure as PNG on the design-system surface and close it."""
    return bk.save(fig, path, formats=("png",), dpi=dpi)[0]


def euro_millions(value: float, _position: int) -> str:
    """Format euros in millions, without Matplotlib offset notation."""
    return f"€{value / 1_000_000:,.1f}M"


def euro_thousands(value: float, _position: int) -> str:
    """Format euros in thousands, without Matplotlib offset notation."""
    return f"€{value / 1_000:,.0f}K"


def plain_number(value: float, _position: int) -> str:
    """Format a numeric tick plainly."""
    return f"{value:,.0f}"


EURO_MILLIONS = FuncFormatter(euro_millions)
EURO_THOUSANDS = FuncFormatter(euro_thousands)
PLAIN_NUMBER = FuncFormatter(plain_number)
