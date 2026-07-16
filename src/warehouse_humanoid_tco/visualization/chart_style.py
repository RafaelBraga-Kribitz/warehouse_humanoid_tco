"""Locked executive-chart palette and formatting helpers."""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter, ScalarFormatter

RECOMMENDED = "#1f77b4"
BASELINE = "#7f7f7f"
OTHER = "#a6c8e0"
ADVERSE = "#d62728"


def apply_style(ax: Axes) -> None:
    """Apply the common restrained style without scientific-offset notation."""
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for axis in (ax.xaxis, ax.yaxis):
        formatter = axis.get_major_formatter()
        if isinstance(formatter, ScalarFormatter):
            formatter.set_scientific(False)
            formatter.set_useOffset(False)


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
