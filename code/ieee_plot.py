"""IEEE two-column figure defaults (~3.5 in column)."""

from pathlib import Path

import matplotlib.pyplot as plt

COL_W = 3.45
FIGDIR = Path(__file__).resolve().parents[1] / "results" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 6.5,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.linewidth": 0.6,
        }
    )


def save(fig, stem: str) -> None:
    fig.savefig(FIGDIR / f"{stem}.png")
    fig.savefig(FIGDIR / f"{stem}.pdf")
    plt.close(fig)
