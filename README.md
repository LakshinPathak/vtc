# vtc

Code and plots for the RSU-TinyGuard sims (VTC-Fall track: IoV / TinyML at the edge).

Working setup: a **relay RSU** that both handles CAM-ish safety traffic and sees IP/flow traffic on the same CPU. A flood is then two separate messes:

1. **Air.** Shared CPU (and optionally occupancy) makes CAM PRR / AoI worse. Detector has to run on the box; waiting for the cloud does nothing for the current subframe.
2. **Ticket.** If you POST the incident over one HTTPS path, a link observer can name the RSU and cut that path.

TinyML classifies on the safety clock (ms). A dumb local map `{none, rate-limit, quarantine}` is the only thing that may change bytes. Incident cloves go out on the report clock (seconds), garlic-bundled so the observer’s AttAcc is not just `φ`. The **gateway is trusted** — it unwraps. Garlic never carries CAM. There is no ns-3 stack in this repo; Plane A PRR comes from the coupling in `code/sim_plane_a_coupling.py`.

Related PerCom tree (FedAvg + ML-KEM, different story): https://github.com/LakshinPathak/ppt-pqc-percom

LaTeX / Overleaf is kept local (`manuscript/`). This repo is scripts, JSON, and figures.

---

## Run

Python 3.10+, CPU torch is enough.

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Drop the Kaggle CSV at

`data/LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv`

(see `data/DATA.md`). It is not in git (~8 MB). JSON in `results/` is enough to read the numbers we already have.

From the **repo root**:

```
python code/train_block_a.py
python code/sim_plane_a_coupling.py
python code/sim_plane_b_garlic.py
python code/make_framework_fig.py
```

Seed 42. Block A is the slow one. Plots land in `results/figures/` (IEEE column width) and `results/block_a/plots/`.

---

## Files

```
code/train_block_a.py          unique-row split, logreg vs TinyMLP, tau / chi
code/sim_plane_a_coupling.py   PRR vs lambda (no-def / detect-only / TinyML+act / oracle)
code/sim_plane_b_garlic.py     N=20, 4000 trials, AttAcc vs T_b and r_c
code/make_framework_fig.py     stack drawing
code/ieee_plot.py              matplotlib defaults
results/block_a/               metrics, .pt, scaler, extra pngs
results/plane_a/coupling_metrics.json
results/plane_b/plane_b_metrics.json
results/figures/               pdf + png
```

D / M / R: TinyML is just `f_θ`. D calls it. Only M may set `a`. Only R packs garlic. Gemini, if you even wire it, is after unwrap.

---

## Dataset (LR-HR DDoS 2024)

Kaggle: abdussalamahmed / LR-HR DDoS 2024 Dataset for SDN-Based Networks. SDN + Ryu, iPerf vs Scapy/Hping3. **Not** a C-V2X trace. Binary `Label` (0/1); LR and HR are mixed in class 1. No packet timestamps. `flow_duration` can be negative — do not treat it as a clock.

Raw file: 113407 rows, 24530 unique? Wait — we measured **43877 unique** after dropping **69530** exact dupes. Raw Label 1 is 70508 because most attack rows are copies; after unique you only have **987** attacks / 42890 benign.

`train_block_a.py` splits unique rows, stratified, scaler fit on train only. Test: 8776 rows, 197 attacks.

On unique rows **every Label 1 flow has `byte_count = 0`**. So `byte_count` cannot be the attack-mass proxy (it is identically 0). We use unit flow mass. If you quote F1 on the undeduplicated CSV you are leaking.

---

## Block A numbers (committed JSON)

Logreg (25 params): acc 0.998, attack F1 **0.949**, ~1.00 AUC. Confusion `[[8559, 20], [1, 196]]`.

TinyMLP 16-8-1 (545 params, ~0.099 ms/flow on the machine we trained on): acc 0.978, attack F1 **0.0**. The saved `tinyml_mlp.pt` predicts all benign on this split (0 TP / 197 FN). Tau sweep therefore quarantines nothing. Dummy rules: `packet_count==0` F1 0.47, `byte_count==0` F1 0.20.

So: logreg is the working tiny baseline in this dump. The MLP checkpoint is a negative result, not a hidden win. Retrain if you want a different head; overwrite JSON and say so.

Actuator (only three actions):

- ŷ = 0 → none, keep 1
- ŷ = 1 and σ ≥ τ → quarantine, keep 0
- ŷ = 1 and σ < τ → rate-limit, keep 0.5

σ = 1 − binary entropy(p) / log 2. χ = fraction of **benign** mass that got rl/q. Detect-only never actuates. Oracle uses the true label and σ=1.

---

## Plane A (coupling)

PRR is **not** from a 3GPP MAC. `sim_plane_a_coupling.py`:

```
rho = clip(0.15 + 0.6 * lam_eff, 0, 1-eps)
cbr = clip(0.20 + 0.5 * lam_eff, 0, 1)
prr = exp(-1.2 * cbr) * (1-rho)^1.5 * (1 - nu * chi)
```

If you only shrink `lam` and never tax FPs, TinyML+act always “wins”. That ranking is vacuous. The interesting comparison is TinyML+act vs detect-only once χ > 0 (`nu` in {0, 0.5, 1}).

The TinyML+act curve in the committed JSON uses an **assumed** operating point `chi=0.001`, attack remain `0.50`. That is **not** taken from the F1=0 checkpoint above. Oracle: lam_eff=0, chi=0.

γ_cpu / α are **not** fitted to a Pi in this dump (`coupling_metrics.json` says so). β>0 means we assume some radio sharing; set β=0 if Uu and PC5 are partitioned.

Figs: `fig3b_prr_coupling`, `fig3c_prr_vs_chi`, `fig3d_dprr_dchi`, `fig3e_rho_ode`.

---

## Plane B (garlic)

`N=20` RSUs, φ=0.5, 4000 trials, m=1 (singleton — the annoying case). Cover r_c in {0,1,3,7}. T_b in {0.5,1,2,5,10} s. Chance is 1/20 = 0.05. T_b is for delay plots; AttAcc in this observer model does not use waiting time.

HTTPS / onion-without-batch sit at AttAcc ≈ φ when the entry is named. Garlic grows mix size with cover. We still need the onion-no-batch row or it just looks like “we used Tor”.

From `results/plane_b/plane_b_metrics.json`:

| | delivery | AttAcc |
|---|---:|---:|
| HTTPS | 0.50 | 0.50 |
| MP-TLS | 0.75 | 0.575 |
| VPN | 0.75 | 0.55 |
| Onion (no mix) | 0.875 | 0.50 |
| Garlic | 0.875 | 0.159 |

Cover byte cost is linear in r_c. Cover is **not** added to Plane A λ. Sister RSUs that are also flooded (mix shrinks) are not in this JSON.

Figs: `fig4a_attacc_vs_tb`, `fig4b_delay_attacc`, `fig4c_baselines_bars`. `framework.png` is the two-plane sketch.

AttAcc is Monte Carlo, not a mixnet proof. Compromised gateway is out of scope.

---

## Citation for the CSV

Ahmed, A. LR-HR DDoS 2024 Dataset for SDN-Based Networks. Kaggle, 2024.  
https://www.kaggle.com/datasets/abdussalamahmed/lr-hr-ddos-2024-dataset-for-sdn-based-networks
