"""RSU-TinyGuard framework figure at PassHy Overleaf size: 1879 x 837 px."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT_DIRS = [
    ROOT / "results" / "figures",
    ROOT / "manuscript" / "figures",
]
W_PX, H_PX, DPI = 1879, 837, 300
W_IN, H_IN = W_PX / DPI, H_PX / DPI

C = {
    "obs": "#E8EEF7",
    "d": "#D6EAF8",
    "m": "#FCE8D5",
    "r": "#EDE7F6",
    "cam": "#FFF3CD",
    "gw": "#F8D7DA",
    "train": "#F4F6F8",
    "edge": "#333333",
    "a": "#1F4E79",
    "b": "#6A1B9A",
}


def box(ax, x, y, w, h, text, fc, fs=7.2, title=None, tw=8.0):
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.07",
            linewidth=1.15,
            edgecolor=C["edge"],
            facecolor=fc,
        )
    )
    if title:
        ax.text(x + 0.08, y + h - 0.16, title, ha="left", va="top", fontsize=tw, fontweight="bold", color="#222")
        ax.text(x + w / 2, y + h / 2 - 0.06, text, ha="center", va="center", fontsize=fs, color="#222")
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#222")


def arrow(ax, x1, y1, x2, y2, color="#333333"):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=9,
            lw=1.15,
            color=color,
            shrinkA=0,
            shrinkB=0,
        )
    )


def main() -> None:
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI)
    ax = fig.add_axes([0.012, 0.02, 0.976, 0.96])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.45)
    ax.axis("off")
    ax.set_aspect("auto")

    ax.text(0.12, 4.32, "RSU-TinyGuard two-plane loop", fontsize=11, fontweight="bold", va="center")
    ax.text(
        9.88,
        4.32,
        r"Safety clock $t$ (ms)  |  Report clock $n$ (s)",
        fontsize=7.4,
        ha="right",
        va="center",
        color="#444",
    )

    # corridor strip
    ax.add_patch(mpatches.FancyBboxPatch((0.12, 3.92), 9.76, 0.28, boxstyle="round,pad=0.01,rounding_size=0.04",
                                         fc="#EEF6EE", ec="#9BB89B", lw=0.7))
    ax.plot([0.3, 9.7], [4.06, 4.06], color="#6B8E6B", lw=1.4, ls="--")
    ax.text(0.35, 4.06, "C-V2X corridor  ·  CAM on air  ·  ITS backhaul on the same RSU CPU",
            fontsize=7.0, va="center", color="#2E4A2E")

    # Plane A band
    ax.add_patch(mpatches.FancyBboxPatch((0.12, 2.18), 9.76, 1.66, boxstyle="round,pad=0.02,rounding_size=0.06",
                                         fc="#F7FBFF", ec="#B7C9DC", lw=0.8))
    ax.text(0.22, 3.72, "Plane A  —  millisecond clock (never waits for garlic or an LLM)",
            fontsize=7.6, fontweight="bold", color=C["a"], va="top")

    box(ax, 0.22, 2.32, 1.72, 1.22,
        "unique 24-D flow $\\mathbf{x}$\nshared CPU / optional CBR\nCAM deadline $T_{\\mathrm{CAM}}$",
        C["obs"], title="RSU observation")
    box(ax, 2.12, 2.32, 1.82, 1.22,
        r"$16$–$8$–$1$ MLP, $545$ params"+"\n"+r"$(\hat{y},\sigma)=f_\theta(\mathbf{x})$"+"\n"+r"$\sigma=1-H(\hat{p})/\log 2$",
        C["d"], title="Detector D  (TinyML)")
    box(ax, 4.12, 2.32, 1.82, 1.22,
        r"$a=\mathcal{M}_{\sigma_{\min}}(\hat{y},\sigma)$"+"\nnone / rate-limit / quarantine\n"+r"keep $\eta(a)$; leftover $\lambda$, $\chi$",
        C["m"], title="Mitigator M")
    box(ax, 6.12, 2.32, 1.82, 1.22,
        r"$\tau_{\mathrm{cpu}}\,\dot{\rho}=-\rho+\cdots$"+"\n"+r"$\mathrm{PRR}=e^{-\gamma_{\mathrm{cbr}}\mathrm{CBR}}(1-\rho)^{\gamma_{\mathrm{cpu}}}(1-\nu\chi)$",
        C["cam"], title="Written CAM coupling")
    box(ax, 8.12, 2.32, 1.62, 1.22,
        "CAM on the air\n"+r"score $\overline{\mathrm{PRR}}$, AoI"+"\nnot a 3GPP stack",
        "#E8F5E9", title="Safety KPI")

    arrow(ax, 1.94, 2.93, 2.12, 2.93, C["a"])
    arrow(ax, 3.94, 2.93, 4.12, 2.93, C["a"])
    arrow(ax, 5.94, 2.93, 6.12, 2.93, C["a"])
    arrow(ax, 7.94, 2.93, 8.12, 2.93, C["a"])

    # Plane B band
    ax.add_patch(mpatches.FancyBboxPatch((0.12, 0.92), 9.76, 1.18, boxstyle="round,pad=0.02,rounding_size=0.06",
                                         fc="#FBF7FF", ec="#C9B7DC", lw=0.8))
    ax.text(0.22, 1.98, "Plane B  —  second clock (ticket only; CAM never in the clove)",
            fontsize=7.6, fontweight="bold", color=C["b"], va="top")

    box(ax, 0.22, 1.02, 1.72, 0.82, "incident declared\nfrom \\texttt{Act}\nno radio command", C["obs"], fs=6.8, title="Act record")
    box(ax, 2.12, 1.02, 1.82, 0.82, r"$c=\mathrm{Enc}_{\mathrm{gw}}(\cdot)$"+"\npseudonym, no CAM", C["r"], fs=6.8, title="Clove")
    box(ax, 4.12, 1.02, 1.82, 0.82, r"wait $T_b$, cover $r_c$"+"\n"+r"mix $\mathcal{U}$, onion if $r_c{=}0$", C["r"], fs=6.8, title="Garlic bulb")
    box(ax, 6.12, 1.02, 1.82, 0.82, "trusted unwrap\noptional LLM note\ncannot emit $a$", C["gw"], fs=6.8, title="Gateway")
    box(ax, 8.12, 1.02, 1.62, 0.82, r"AttAcc vs $\phi$"+"\nDeliv vs hops\nMonte Carlo", "#FFEBEE", fs=6.8, title="Plane B KPI")

    # dashed down from M/Act to Plane B (clock break)
    ax.annotate(
        "",
        xy=(1.08, 1.84),
        xytext=(5.03, 2.32),
        arrowprops=dict(arrowstyle="-|>", color=C["b"], lw=1.05, ls="--"),
    )
    ax.text(3.35, 2.12, "report clock $n$ only", fontsize=6.4, color=C["b"], ha="center")

    arrow(ax, 1.94, 1.43, 2.12, 1.43, C["b"])
    arrow(ax, 3.94, 1.43, 4.12, 1.43, C["b"])
    arrow(ax, 5.94, 1.43, 6.12, 1.43, C["b"])
    arrow(ax, 7.94, 1.43, 8.12, 1.43, C["b"])

    # training bar
    ax.add_patch(mpatches.FancyBboxPatch((0.12, 0.08), 9.76, 0.76, boxstyle="round,pad=0.02,rounding_size=0.06",
                                         fc=C["train"], ec="#C5CCD4", lw=0.8))
    ax.text(0.22, 0.72, "Offline (unique-row split)", fontsize=7.4, fontweight="bold", va="top")
    box(ax, 0.22, 0.16, 2.35, 0.42, "drop $69{,}530$ duplicates first\n$28080/7021/8776$, scaler on train", C["obs"], fs=6.4)
    box(ax, 2.70, 0.16, 2.35, 0.42, r"BCE on unique train rows"+"\n"+r"attack $F_1{=}0.963$ at $0.10$ ms", C["d"], fs=6.4)
    box(ax, 5.18, 0.16, 2.35, 0.42, "least privilege: D, M, R\nlater stages cannot command earlier", C["m"], fs=6.4)
    box(ax, 7.66, 0.16, 2.08, 0.42, "LLM after unwrap only\nnot on the safety clock", C["gw"], fs=6.4)

    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        png = d / "framework.png"
        pdf = d / "framework.pdf"
        fig.savefig(png, dpi=DPI, facecolor="white")
        fig.savefig(pdf, facecolor="white")
        print("wrote", png)

    plt.close(fig)


if __name__ == "__main__":
    main()
