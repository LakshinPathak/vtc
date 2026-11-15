"""Plane A coupling curves from PAPER_STORY §1.4 (unit-flow mass)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ieee_plot import COL_W, apply_style, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "plane_a"
OUT.mkdir(parents=True, exist_ok=True)

RHO0, CBR0 = 0.15, 0.20
ALPHA, BETA = 0.6, 0.5
G_CBR, G_CPU = 1.2, 1.5
NU, EPS, T_CAM = 1.0, 1e-3, 0.100


def prr(lam_att_eff: float, chi: float, beta: float = BETA, nu: float = NU) -> float:
    rho = np.clip(RHO0 + ALPHA * lam_att_eff, 0.0, 1.0 - EPS)
    cbr = np.clip(CBR0 + beta * lam_att_eff, 0.0, 1.0)
    phys = np.exp(-G_CBR * cbr) * (1.0 - rho) ** G_CPU
    return float(phys * (1.0 - nu * chi))


def main() -> None:
    apply_style()
    import matplotlib.pyplot as plt

    lam = np.linspace(0.0, 1.0, 21)
    # Unique-split TinyMLP+act at tau that rate-limits all detections (sigma low):
    # chi~0.0007, att_remain~0.51 from first good run; use 0.001 and 0.50.
    chi_act, remain = 0.001, 0.50
    series = {
        "no defense": [prr(l, 0.0) for l in lam],
        "detect-only": [prr(l, 0.0) for l in lam],
        r"TinyML+act": [prr(remain * l, chi_act) for l in lam],
        "oracle": [prr(0.0, 0.0) for _ in lam],
    }
    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    for k, ys in series.items():
        ax.plot(lam, ys, marker="o", markersize=2.5, label=k)
    ax.set_xlabel(r"offered attack intensity $\lambda^{\mathrm{att}}$")
    ax.set_ylabel("CAM PRR (coupling)")
    ax.legend()
    ax.set_ylim(0, 1.02)
    save(fig, "fig3b_prr_coupling")

    # nu sweep at lambda=0.6: TinyML FPR chi from 0 to 0.2
    chi_grid = np.linspace(0, 0.2, 9)
    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    for nu, ls in [(0.0, "--"), (0.5, "-."), (1.0, "-")]:
        ys = [prr(remain * 0.6, c, nu=nu) for c in chi_grid]
        ax.plot(chi_grid, ys, ls, marker="s", markersize=3, label=rf"$\nu={nu}$")
    ax.axhline(prr(0.6, 0.0), color="0.5", lw=0.8, label="detect-only")
    ax.set_xlabel(r"collateral $\chi$")
    ax.set_ylabel("CAM PRR")
    ax.legend()
    save(fig, "fig3c_prr_vs_chi")

    # Sensitivity: partial PRR / partial chi = -nu * phys (independent of chi)
    lam_s = 0.6
    rho_s = np.clip(RHO0 + ALPHA * remain * lam_s, 0.0, 1.0 - EPS)
    cbr_s = np.clip(CBR0 + BETA * remain * lam_s, 0.0, 1.0)
    phys_s = float(np.exp(-G_CBR * cbr_s) * (1.0 - rho_s) ** G_CPU)
    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    nus = np.array([0.0, 0.5, 1.0])
    dprr = -nus * phys_s
    ax.bar(["0", "0.5", "1"], -dprr, color=["0.75", "0.45", "0.2"])
    ax.set_xlabel(r"collateral weight $\nu$")
    ax.set_ylabel(r"$-\partial\mathrm{PRR}/\partial\chi$ at $\lambda{=}0.6$")
    save(fig, "fig3d_dprr_dchi")

    # Occupancy lag ODE vs offered attack step
    tau_cpu = 0.02  # uncalibrated, 20 ms software pipeline
    t = np.linspace(0, 0.2, 201)
    lam_step = 0.8
    rho_inf = np.clip(RHO0 + ALPHA * lam_step, 0.0, 1.0 - EPS)
    rho_t = rho_inf + (RHO0 - rho_inf) * np.exp(-t / tau_cpu)
    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    ax.plot(t * 1e3, rho_t, label=r"$\rho(t)$ ODE")
    ax.axhline(rho_inf, color="0.4", ls="--", lw=0.8, label=r"steady $\rho$")
    ax.set_xlabel("time after attack step (ms)")
    ax.set_ylabel("CPU occupancy")
    ax.legend()
    ax.set_ylim(0, 1.0)
    save(fig, "fig3e_rho_ode")

    payload = {
        "lambda": lam.tolist(),
        "series": series,
        "defaults": {
            "rho0": RHO0,
            "cbr0": CBR0,
            "alpha": ALPHA,
            "beta": BETA,
            "gamma_cbr": G_CBR,
            "gamma_cpu": G_CPU,
            "nu": NU,
        },
        "tinyml_act_at_lam": {"chi": chi_act, "attack_remain": remain},
        "note": "CPU exponents uncalibrated until Pi replay; ranking uses nu>0.",
    }
    (OUT / "coupling_metrics.json").write_text(json.dumps(payload, indent=2))
    print("wrote", OUT / "coupling_metrics.json")


if __name__ == "__main__":
    main()
