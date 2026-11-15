# vtc (RSU-TinyGuard experiments)

Simulation code for **two-plane DDoS response** at a **simulated** C-V2X / RSU edge:

- **Plane A (air / CAM availability).** TinyML on unique SDN flows plus a *stated* CPU/CBR coupling model. Remaining attack load and false-positive collateral (`χ`) map onto CAM packet reception ratio (PRR) and age of information (AoI). This is **not** a 3GPP PHY/MAC stack.
- **Plane B (ticket / identity).** Garlic-bundled incident cloves on the **backhaul**, compared with HTTPS, multipath TLS, VPN, and onion-without-batching, under a **link observer** who sees entry metadata with probability `φ`.

This GitHub tree is **Python + JSON logs + figures**. It is **not** the paper. There is no LaTeX, IEEE class file, or camera-ready PDF here.

What the experiments actually implement:

| Program | Question | Code |
|---------|----------|------|
| Block A | After dropping duplicate CSV rows, can a 545-parameter TinyMLP (and a 25-parameter logreg) see Label 1, and how fast is a CPU forward pass? | `train_block_a.py` |
| Plane A | If the actuator changes attack remain and collateral `χ`, how does the coupling PRR rank no-defense / detect-only / TinyML+act / oracle? | `sim_plane_a_coupling.py` |
| Plane B | If a link observer sees mix entry with probability `φ`, how does AttAcc change with batch window `T_b` and cover `r_c`, vs HTTPS / MP-TLS / VPN / onion? | `sim_plane_b_garlic.py` |

Two clocks stay separate. They are never mixed in the metrics:

| Clock | Timescale | What runs |
|-------|-----------|-----------|
| Safety | milliseconds | TinyML score + local actuator (`none` / rate-limit / quarantine) |
| Report | seconds | Encrypted incident clove, garlic mix, gateway unwrap |

The **gateway is trusted** to unwrap cloves. Garlic never carries CAM. Gemini (if used at all) is after unwrap only; it does not command the radio. There is no live C-V2X radio, no NS-3, and no real mixnet in this tree.

AttAcc is a **Monte Carlo model statistic**, not an anonymity proof.

---

## 1. What an “RSU” is in this repo

There is no roadside hardware. The evaluation RSU is a **relay / edge box** that:

1. participates in CAM-like safety traffic (hears and/or forwards),
2. terminates or forwards IP/flow traffic on a shared CPU (and optionally a shared occupancy term),
3. must notify an operator when it is under flood.

A flood on the flow table hurts CAM **only through the coupling in `sim_plane_a_coupling.py`**, not by claiming the Kaggle CSV *is* NR-V2X IQ.

Labels come from the public LR-HR DDoS 2024 SDN table ([Kaggle](https://www.kaggle.com/datasets/abdussalamahmed/lr-hr-ddos-2024-dataset-for-sdn-based-networks)): `Label=0` normal, `Label=1` malicious (low-rate and high-rate in **one** class). SDN/Mininet + Ryu; iPerf normal; Scapy/Hping3 malicious.

**Primary bottleneck (always on in the coupling):** shared CPU / packet pipeline. Offered flood load raises utilization `ρ`. CAM-like frames that miss a software deadline are dropped even if the air was free.

**Secondary bottleneck (on when `β > 0`):** shared occupancy. Flood bytes raise CBR. If radio is partitioned, set `β = 0` and keep CPU coupling only.

---

## 2. Setup

Python 3.10+ (3.12 is fine). CPU PyTorch is enough.

```bash
git clone https://github.com/LakshinPathak/vtc.git
cd vtc
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt`: `torch`, `numpy`, `pandas`, `scikit-learn`, `matplotlib`.

### Dataset

Put the CSV at:

```
data/LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv
```

See [`data/DATA.md`](data/DATA.md). The CSV is gitignored (~8 MB). Committed JSON under `results/` is enough to inspect numbers. Retraining Block A needs the file.

---

## 3. Reproduce

Run from the **repository root** (scripts resolve `../data` and `../results` from `code/`).

```bash
python code/train_block_a.py
python code/sim_plane_a_coupling.py
python code/sim_plane_b_garlic.py
python code/make_framework_fig.py   # optional stack drawing
```

`ieee_plot.py` writes IEEE column-width PDFs/PNGs to `results/figures/`.

Block A training is the slow step. Plane A/B are seconds. Seed **42** unless a script says otherwise.

---

## 4. Layout

```
code/
  train_block_a.py          unique split, TinyMLP, logreg, actuator / chi
  sim_plane_a_coupling.py   CAM PRR vs lambda (no-defense, detect-only, TinyML+act, oracle)
  sim_plane_b_garlic.py     link-observer Monte Carlo (N=20 RSUs, 4000 trials)
  make_framework_fig.py     two-plane stack drawing
  ieee_plot.py              figure style and save paths
data/
  DATA.md                   how to obtain the CSV (CSV itself is gitignored)
results/block_a/            detector JSON, train history, extra plots, scaler, .pt
results/plane_a/            coupling_metrics.json
results/plane_b/            plane_b_metrics.json
results/figures/            paper-style PDFs and PNGs
```

---

## 5. Permissioned pipeline (D / M / R)

TinyML is a **function** (window → class, `σ`). It is not a process and is not an “agent.”

| Role | Tools | Clock |
|------|-------|-------|
| **D** detector | invoke `f_θ` only; publish `Detect{y,σ,t}` | safety (ms) |
| **M** mitigator | `none` / `rl` / `q` only; never Gemini | safety (ms) |
| **R** reporter | pack clove, garlic bulb; cannot emit `Act` | report (s) |
| Gateway | unwrap; optional Gemini after unwrap | report (s) |

```
  x_t, coupling(CBR, PRR)
           │
           ▼
   ┌───────────────┐   Detect{y,σ,t}   ┌───────────────┐
   │  D  (TinyML)  │ ────────────────► │  M  (rules)   │
   └───────────────┘                   └───────┬───────┘
                                               │ Act{a, CBR, t}
                                               ▼
                                       ┌───────────────┐
                                       │  R  (garlic)  │
                                       └───────┬───────┘
                                               │ seconds, bulbs
                                               ▼
                                       Gateway (trusted unwrap)
```

Downstream cannot command upstream. Unknown class (not present in this binary CSV) maps to `none`, not quarantine.

---

## 6. Block A: unique-row detector

### Split

`train_block_a.py` does **not** use the leaky Kaggle notebook: it drops exact duplicates before split, stratifies on `Label`, and fits `StandardScaler` on **train only**. LSTM/GRU-on-24-unordered-features is omitted (not a sequence).

| | |
|--|--|
| Raw rows | 113,407 × 25 (24 features + `Label`) |
| Unique | **43,877** (69,530 duplicates dropped) |
| Unique labels | 42,890 benign / **987** attack (raw Label 1 was 70,508 mostly copies) |
| Features | 24 numeric (see `results/block_a/dataset_meta.json`) |
| Test | 8,776 rows, **197** attacks |
| Seed | 42 |

**Shortcut that must be disclosed.** On unique rows, **every Label 1 flow has `byte_count = 0`**. `byte_count > 0` implies benign. Do **not** put `byte_count` into attack intensity. Collateral and remaining attack use **unit flow mass** (see comments in `train_block_a.py`). There are **no timestamps**; `flow_duration` can be negative and is not a clock.

### Actuator

Confidence `σ = 1 − H(p)/log 2`. Keep fractions: `η(none)=1`, `η(rl)=0.5`, `η(q)=0`.

| Prediction | σ vs τ | Action | Byte keep η |
|------------|---------|--------|-------------|
| benign | any | none | 1 |
| attack | σ ≥ τ | quarantine | 0 |
| attack | σ < τ | rate-limit | 0.5 |

`χ` = fraction of **benign** mass dropped or rate-limited. Detect-only never actuates (`χ=0`). Oracle uses true labels (`σ=1`): quarantine all attacks, never touch benign.

### Committed metrics (`results/block_a/block_a_metrics.json`)

| Model | Params | Accuracy | Attack F1 | ROC-AUC | Notes |
|-------|-------:|---------:|----------:|--------:|-------|
| Logistic regression | 25 | 0.998 | **0.949** | ~1.00 | confusion [[8559, 20], [1, 196]] |
| TinyMLP `16-8-1` | 545 | 0.978 | **0.0** | 0.832 | all-benign on this checkpoint; ~**0.099 ms/flow** CPU |

**Read the TinyMLP row carefully.** The committed `.pt` predicts **zero true positives** on the unique test split (0 TP / 197 FN). Tau-sweep quarantine counts are therefore zero. Logreg is the working tiny linear baseline. A dummy rule `packet_count == 0` has attack F1 0.47; `byte_count == 0` has F1 0.20.

If you retrain, compare new JSON to this file before quoting F1. F1 is **feasibility** for `f_θ`, not the main Plane A KPI.

---

## 7. Plane A coupling (PRR plots)

Ranking `no-defense < detect-only < TinyML+act < oracle` that only reduces attack `λ` is **vacuous** (PRR is monotone in remaining attack). The ranking that can **flip** is TinyML+act vs detect-only, once false-positive actions tax benign mass.

Defaults in `sim_plane_a_coupling.py`:

```
ρ   = clip(ρ0 + α λ_att_eff, 0, 1-ε)
CBR = clip(CBR0 + β λ_att_eff, 0, 1)
PRR = exp(-γ_cbr CBR) * (1-ρ)^γ_cpu * (1 - ν χ)
AoI = T_CAM / (PRR + ε)
```

with `ρ0=0.15`, `CBR0=0.20`, `α=0.6`, `β=0.5`, `γ_cbr=1.2`, `γ_cpu=1.5`, `ν=1`, `T_CAM=100 ms`.

| Method | `λ_att_eff` | `χ` |
|--------|-------------|-----|
| no defense | `λ` | 0 |
| detect-only | `λ` | 0 |
| TinyML+act | `0.50 λ` | 0.001 |
| oracle | 0 | 0 |

The TinyML+act row is a **parametric operating point** (`chi ≈ 0.001`, remain `0.50`) used to draw curves. It is **not** a claim that the committed MLP checkpoint achieves 50% attack-mass removal (that checkpoint currently detects nothing). Sweep `ν ∈ {0, 0.5, 1}`: `ν=0` recovers the vacuous ranking; `ν>0` lets TinyML+act **lose** to detect-only when FPR is high.

CPU exponents in the committed JSON are **uncalibrated** (no Raspberry Pi replay of CAM deadline-miss vs attack byte rate). CBR exponent is assumed whenever `β>0`.

JSON: `results/plane_a/coupling_metrics.json`.

---

## 8. Plane B mix (link observer)

Clove (report clock `n`): encrypt `(ŷ, σ, a, CBR before/after, PRR, RSU pseudonym)` for the **gateway only**. Bulb = real cloves + cover cloves. RSUs do not hold a Gemini key. We **do not** claim anonymity against the gateway.

Adversary `A_B` does not control the gateway. It observes a fraction `φ` of backhaul links (timing, size, next hop). No plaintext cloves.

`sim_plane_b_garlic.py`: `N=20` RSUs, `φ=0.5`, 4000 Monte Carlo trials, seed 42, chance `1/N = 0.05`. Incidents per epoch default `m=1` (hard case: singleton). Cover `r_c ∈ {0,1,3,7}`. Window `T_b ∈ {0.5, 1, 2, 5, 10}` s. Waiting `T_b` is swept; AttAcc should stay flat in `T_b` if the observer model does not use delay.

Garlic = layered path hiding **plus batching plus cover**. Distinguishing ablation is **onion, no batch, no cover**.

| Path | Delivery (committed) | AttAcc (committed) | Observer |
|------|---------------------:|-------------------:|----------|
| HTTPS | 0.50 | 0.50 | named if Gemini path ∈ observed links |
| MP-TLS | 0.75 | 0.575 | endpoints still named |
| VPN | 0.75 | 0.55 | tunnel endpoints named |
| Onion (no mix) | 0.875 | 0.50 | singleton timing/size |
| Garlic | 0.875 | **0.159** | mix size = real + cover |

Cover overhead is linear in `r_c` (`rel_overhead = r_c`). Cover is Plane B only in this code (not added to `λ_att`). Sister-RSU failure (flooded or lying) is **not** simulated in the committed JSON.

JSON: `results/plane_b/plane_b_metrics.json`.

---

## 9. Figures

Under `results/figures/`:

| File | Content |
|------|---------|
| `framework.pdf` / `.png` | Two-plane stack drawing |
| `fig3b_prr_coupling` | PRR vs offered attack intensity |
| `fig3c_prr_vs_chi` | PRR vs collateral `χ` at `λ=0.6` |
| `fig3d_dprr_dchi` | `−∂PRR/∂χ` vs `ν` |
| `fig3e_rho_ode` | CPU occupancy after an attack step (uncalibrated 20 ms lag) |
| `fig4a_attacc_vs_tb` | AttAcc vs garlic window `T_b` |
| `fig4b_delay_attacc` | delay vs attribution |
| `fig4c_baselines_bars` | HTTPS / MP-TLS / VPN / onion / garlic |

Extra Block A plots (ROC, confusion, tau sweep) sit in `results/block_a/plots/`. Weights: `results/block_a/tinyml_mlp.pt`. Scaler: `results/block_a/split_scaler.npz`.

---

## 10. What this repo does not contain

- VTC LaTeX / bibliography / Overleaf project.
- Internal planning notes.
- The LR-HR CSV.
- ns-3, C-V2X PHY, or a fitted Raspberry Pi calibration of `α, γ_cpu`.
- A deployed garlic overlay.
- ML-KEM / post-quantum wrap (that is a different tree: [ppt-pqc-percom](https://github.com/LakshinPathak/ppt-pqc-percom)).
- Anonymity against the trusted gateway.
- Gemini as classifier or actuator.
- Relabeling CIC-style features as NR-V2X IQs.

Out of scope for the observer model: compromised gateway, poisoned TinyML, correlation across report slots.

A later write-up is **wrong** if it: puts CAM in a bulb; calls garlic the C-V2X radio defense; puts an LLM on the safety clock; reports F1 on undeduplicated rows; uses a monotone-in-`λ` ranking without `χ`; claims unlinkability from the gateway; omits onion-no-batch; treats LR-HR 2024 as a C-V2X trace or as timed windows.

---

## 11. Data citation

Ahmed, A. *LR-HR DDoS 2024 Dataset for SDN-Based Networks*. Kaggle, 2024.  
https://www.kaggle.com/datasets/abdussalamahmed/lr-hr-ddos-2024-dataset-for-sdn-based-networks
