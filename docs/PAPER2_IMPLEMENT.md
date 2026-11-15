# Paper 2 implementation punch list

Story: `PAPER2_STORY.md`. BB84 seat: `PAPER2_BB84_HOOK.md`. Do **not** edit Paper 1 manuscript or overwrite `vtc/results/block_a/`.

Work in order. **Stop at each gate.** BB84 is last.

Output root: `vtc/results/paper2/`  
Figures: `vtc/results/paper2/figures/` and copy PNG to `vtc/manuscript_paper2/figures/` when that folder exists.

Python: project `.venv`, PyTorch for TinyML (same 16-8-1 as the unique-split trainer). Not the Kaggle Keras federated notebook.

---

## Phase 0 — shared data (no training yet)

**Build.** Reuse unique load + split. Do not fit the scaler on all rows.

| Item | Spec |
|---|---|
| CSV | `vtc/data/LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv` |
| Drop exact duplicates first | raw 113407 → unique 43877 (42890 / 987) |
| Split | seed 42, stratified, 28080 / 7021 / 8776 |
| Scaler | train only |
| Test | frozen forever, never a client |

**Write.** `vtc/results/paper2/split_meta.json` (counts, per-label, seed).

**Gate 0.** Label-1 in test is 197-ish (unique split). If test still has leaked duplicates from the raw file, stop.

---

## Phase 1 — federated TinyML (Plane M)

**Build.** `vtc/code/train_fed.py`

| Method | Meaning |
|---|---|
| P | pooled TinyML on all unique train (upper bound) |
| L | each client local TinyML, each scored on **global test**, mean ± std attack F1 |
| F-IID | FedAvg, stratified unique train across K |
| F-SK | FedAvg, most Label-1 train rows on 1–2 clients |
| MED | coordinate-wise median of client weights, same shards as F-SK (and poison) |

**Model.** 16-8-1, ~545 params, CPU, BCE with `pos_weight` if all-benign. No LSTM. No temperature unless you also report F1=0.

**Knobs after pilot freeze.** K in {5,10,20}. Rounds R=20. Local epochs E=2. Batch 256. Adam 1e-3. C=1 (all clients). Seed 42.

**Pilot first.** K=5, R=5, P vs L vs F-IID only.

**Write.** `vtc/results/paper2/fl_metrics.json`  
Per method: accuracy (footnote), **attack F1**, confusion, rounds, K, Label-1 count per client (T1).

**Plots (IEEE, `ieee_plot.py` style).**

| File | Content |
|---|---|
| `fig_p2_f1_vs_round.png` | attack F1 vs round, P as hline, F-IID, F-SK, L mean |
| `fig_p2_f1_bars.png` | final attack F1: L, P, F-IID, F-SK, MED at K=10 |
| `fig_p2_f1_vs_K.png` | attack F1 vs K for F-IID and F-SK |

**Gate 1.**

- F-IID attack F1 ≈ 0 (all benign) → fix pos_weight / E. Do not start garlic.  
- F-IID ≈ F-SK ≈ P because duplicates leaked → fix partition.  
- F-IID within ~0.03 of P, later F-SK worse → continue.  
- Do not claim beating P as success.

**Poison (same phase, after Gate 1).** n_bad in {0,1,2}: label-flip on that client’s Label-1. Plot `fig_p2_f1_vs_nbad.png` FedAvg vs MED. Garlic is **not** this defense.

---

## Phase 2 — onion / garlic on **weight** parcels (Plane U)

**Build.** `vtc/code/sim_plane_u_garlic.py`  
Clone the idea of the existing mix observer, but:

- payload = TinyML weights (~545 × 4 B ≈ 2.2 KB), not a ticket, not CAM
- N = K (same as federated clients)
- φ = 0.5
- r_c in {0,1,3,7}, T_b in {0.5, 2, 5, 10} s
- HTTPS, onion without mix (r_c=0, T_b→0), garlic
- Do **not** invent VPN/MP-TLS AttAcc unless you write a real model

**Write.** `vtc/results/paper2/plane_u.json`

**Plots.**

| File | Content |
|---|---|
| `fig_p2_attacc_vs_tb.png` | AttAcc vs T_b for each r_c |
| `fig_p2_delivery_attacc.png` | bars: delivery under path cut vs AttAcc for named path, onion, garlic |
| `fig_p2_bytes_vs_f1.png` | comm bytes (updates × rounds × (1+r_c)) vs attack F1 (uses Phase 1 F1) |

**Gate 2.** Named path and onion-without-mix AttAcc ≈ φ. Garlic AttAcc drops only when mix size > 1. If garlic equals onion at r_c=0, that is correct, not a bug.

---

## Phase 3 — tables for the manuscript (no BB84 yet)

| Table | Content |
|---|---|
| T1 | unique split + per-client Label-1 counts IID vs SK |
| T2 | L, P, F-IID, F-SK, MED: acc footnote, attack F1, params, R, E, bytes |
| T3 | Plane U: AttAcc, delay T_b/2, cover, N, φ, payload size in caption |

Paper 2 manuscript folder can wait until T2 exists.

---

## Phase 4 — BB84 trunk (optional, last)

**Do not start** until Gate 1 and Gate 2 pass, and you explicitly ask for the trunk.

**Build (only then).** `vtc/code/sim_bb84_trunk.py`

- **Where:** mix gateway ↔ collector only (step 5 in `PAPER2_BB84_HOOK.md`).  
- **Output:** night key K (do not feed it into FedAvg). QBER vs a toy intercept-resend Eve on that trunk.  
- **Then:** AES-K is a **label** in the diagram/story, not a TinyML input.  
- Simulator **outside** the averaging loop. Qiskit allowed here only.

**Forbidden in this file.** Pole→collector BB84. BB84 before mix. Day path. Inside median. Inside training. “Quantum TinyML.” “BB84 is garlic.” “BB84 stops a liar.” “Quantum CAM.” “BB84 improved F1.” “Real QKD hardware.”

**Plots (optional).**

| File | Caption must say |
|---|---|
| `fig_p2_qber_vs_eve.png` | trunk simulation, AttAcc unchanged |
| `fig_p2_sifted_bits.png` | optional, same caption |

**Write.** `vtc/results/paper2/bb84_trunk.json` (QBER, sifted bits, n_qubits or n_pulses, Eve strength). No attack F1 field unless copied unchanged from Phase 1 with a note “not produced by BB84.”

**Gate 4.** If a plot implies F1 or AttAcc moved, delete the figure.

---

## What you implement vs what you do not

**Do**

- Unique split, train-only scaler  
- P, L, F-IID, F-SK, MED, poison n_bad  
- Garlic vs onion vs named path on **weights**  
- IEEE bar/line plots above  
- BB84 **only** after the gates, trunk only  

**Do not**

- Touch Paper 1 `vtc/manuscript/main.tex` or `block_a_metrics.json`  
- Keras Kaggle federated script (scaler on all data, no dedup, log_loss on hard labels, client F1 on train rows)  
- LSTM, CAM in a bulb, FedAvg inside the daytime act  
- VPN/MP-TLS fake AttAcc  
- Qiskit inside `train_fed.py`

---

## Suggested order of commands (when you run)

1. Unique split meta → Gate 0  
2. Pilot `train_fed.py` K=5 R=5 P/L/F-IID → Gate 1  
3. Full F-SK, K sweep, MED, poison → Phase 1 plots  
4. `sim_plane_u_garlic.py` → Gate 2 → Phase 2 plots  
5. T1–T3  
6. Only if asked: `sim_bb84_trunk.py` → QBER figure  

---

## Definition of done (Paper 2 experiments)

- [ ] `split_meta.json`  
- [ ] `fl_metrics.json` with P, L, F-IID, F-SK, MED  
- [ ] `fig_p2_f1_vs_round.png` `fig_p2_f1_bars.png` `fig_p2_f1_vs_K.png` `fig_p2_f1_vs_nbad.png`  
- [ ] `plane_u.json`  
- [ ] `fig_p2_attacc_vs_tb.png` `fig_p2_delivery_attacc.png` `fig_p2_bytes_vs_f1.png`  
- [ ] T1–T3 numbers filled from JSON  
- [ ] BB84 files **absent** unless Gate 1–2 passed and you asked for Phase 4  

That is the full implementation list. Story first, federated second, mix third, BB84 last.
