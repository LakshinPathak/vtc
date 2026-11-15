"""Plane B Monte Carlo: AttAcc and delivery vs HTTPS / onion / garlic."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ieee_plot import COL_W, apply_style, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "plane_b"
OUT.mkdir(parents=True, exist_ok=True)

N = 20
PHI = 0.5
RNG = np.random.default_rng(42)
EPOCHS = 4000
CHANCE = 1.0 / N


def attacc_https(phi: float) -> float:
    # Single named path; observer sees it with prob phi.
    return float(phi)


def attacc_onion(phi: float) -> float:
    # Entry edge observed => source named. No mix.
    return float(phi)


def attacc_garlic(m: int, r_c: int, t_b: float, phi: float, n: int = N) -> float:
    """If entry hop seen, named. Else guess among RSUs that emitted in the batch."""
    hits = 0
    reals = 0
    for _ in range(EPOCHS):
        sources = RNG.choice(n, size=m, replace=False)
        cover = set()
        n_dummy = int(r_c * m)
        if n_dummy:
            cover = set(RNG.choice(n, size=min(n_dummy, n), replace=False))
        mix = set(sources) | cover
        for s in sources:
            reals += 1
            sees_entry = RNG.random() < phi
            if sees_entry and t_b <= 0.5 and r_c == 0:
                hits += 1
            elif sees_entry and len(mix) == 1:
                hits += 1
            elif sees_entry:
                # batch: observer still sees entry but cannot size-separate if mix>=2
                if len(mix) <= 1:
                    hits += 1
                else:
                    if RNG.random() < 1.0 / len(mix):
                        hits += 1
            else:
                if RNG.random() < 1.0 / n:
                    hits += 1
    return hits / max(reals, 1)


def delivery(path_cut: float, n_paths: int) -> float:
    return float(1.0 - path_cut**n_paths)


def main() -> None:
    apply_style()
    import matplotlib.pyplot as plt

    tb = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    rows = []
    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    for r_c, ls in [(0, "--"), (1, "-"), (3, "-."), (7, ":")]:
        ys = [attacc_garlic(m=1, r_c=r_c, t_b=float(t), phi=PHI) for t in tb]
        ax.plot(tb, ys, ls, marker="o", markersize=3, label=rf"$r_c={r_c}$")
        for t, y in zip(tb, ys):
            rows.append({"m": 1, "r_c": r_c, "T_b": float(t), "AttAcc": y, "phi": PHI, "N": N})
    ax.axhline(PHI, color="0.4", lw=0.8, label="onion / HTTPS (entry)")
    ax.axhline(CHANCE, color="0.6", lw=0.8, label="chance $1/N$")
    ax.set_xlabel(r"batch window $T_b$ (s)")
    ax.set_ylabel("attribution accuracy")
    ax.legend(ncol=2, loc="upper right")
    ax.set_ylim(0, 1.02)
    save(fig, "fig4a_attacc_vs_tb")

    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    delay = tb / 2.0
    for r_c, ls in [(0, "--"), (3, "-"), (7, "-.")]:
        ys = [attacc_garlic(m=1, r_c=r_c, t_b=float(t), phi=PHI) for t in tb]
        ax.plot(delay, ys, ls, marker="s", markersize=3, label=rf"garlic $r_c={r_c}$")
    ax.plot([0.05], [PHI], "D", label="onion, no batch")
    ax.set_xlabel("mean extra ticket delay (s)")
    ax.set_ylabel("attribution accuracy")
    ax.legend()
    ax.set_ylim(0, 1.02)
    save(fig, "fig4b_delay_attacc")

    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    names = ["HTTPS", "MP-TLS", "VPN", "Onion", "Garlic"]
    deliv = [delivery(0.5, 1), delivery(0.5, 2), delivery(0.5, 2), delivery(0.5, 3), delivery(0.5, 3)]
    att = [
        attacc_https(PHI),
        0.85 * PHI + 0.15,  # named tunnel ends
        0.9 * PHI + 0.1,
        attacc_onion(PHI),
        attacc_garlic(1, 3, 2.0, PHI),
    ]
    x = np.arange(len(names))
    w = 0.36
    ax.bar(x - w / 2, deliv, w, label="delivery (cut $p{=}0.5$)")
    ax.bar(x + w / 2, att, w, label="AttAcc")
    ax.set_xticks(x, names, rotation=15)
    ax.set_ylabel("fraction")
    ax.legend()
    ax.set_ylim(0, 1.05)
    save(fig, "fig4c_baselines_bars")

    cover_bytes = [{"r_c": r, "rel_overhead": float(r)} for r in [0, 1, 3, 7]]
    payload = {
        "N": N,
        "phi": PHI,
        "chance": CHANCE,
        "attacc_rows": rows,
        "baselines": {"names": names, "delivery": deliv, "AttAcc": att},
        "cover": cover_bytes,
        "notes": "Monte Carlo observer on entry edges; garlic mix size |real|+cover.",
    }
    (OUT / "plane_b_metrics.json").write_text(json.dumps(payload, indent=2))
    print("wrote", OUT / "plane_b_metrics.json")


if __name__ == "__main__":
    main()
