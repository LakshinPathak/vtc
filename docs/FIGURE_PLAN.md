# Five-page IEEE two-column figure budget

VTC-Fall camera-ready is typically **5 pages + refs**. This pack generates extra PNGs; **only the rows marked PAPER** go in `main.tex`. Extra plots are supplements.

| Slot | Kind | File stem | Why |
|---|---|---|---|
| Fig. 1 | system (later TikZ) | `(tex)` | Two planes, two clocks — not a training plot |
| Fig. 2 PAPER | 2-panel bars + ROC | `fig2_block_a_bars_roc` | Detector is feasible and Tiny vs LSTM/GRU size |
| Fig. 3 PAPER | lines | `fig3_tau_chi_prr` | Non-vacuous ranking: χ vs leftover attack; PRR vs method |
| Fig. 4 PAPER | lines | `fig4_garlic_attacc` | AttAcc vs \(T_b\); delay–AttAcc frontier vs onion |
| Tab. 1 | related work | (tex) | IEEE V2X DDoS / TinyML / I2P-garlic |
| Tab. 2 | Block A KPIs | (tex from JSON) | unique-split F1, params, ms/flow |
| Tab. 3 | Plane B | (tex from JSON) | HTTPS / onion / garlic delivery + AttAcc |

**Do not put in 5 pages:** raw-vs-unique class bars (one sentence in text), per-model confusion heatmaps (optional 2-col if space), Gemini latency (one sentence).

Train first; drop figures if Overleaf overflows page 5.
