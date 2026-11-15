# RSU-TinyGuard: Two-Plane DDoS Response at the C-V2X / RSU Edge

**Working title.** TinyML detection and garlic-routed incident reporting for radio-aware DDoS response at the C-V2X RSU edge.

**Venue.** IEEE VTC-Fall 2027 (Osaka). Tracks: IoV / IoT / M2M; AI and machine learning for communications.

**This file.** Problem statement and story lock. Plane A uses an **explicit coupling model** (not a hidden 3GPP stack). Plane B has its **own threat model**. D/M/R are **permissioned processes** (least privilege, clock separation); “agent” is optional wording, not the claim. Not a manuscript.

**One-line claim.** A flood on a **relay RSU** is two failures at once: the **air** (shared CPU/radio makes CAM PRR/AoI collapse) and the **ticket** (who reported, on which path). TinyML classifies on the box; a local actuator protects CAM in milliseconds. Incident **cloves** are garlic-bundled on the backhaul so a **link observer** cannot attribute the source RSU as cheaply as under clear HTTPS, multipath TLS, VPN, or onion-without-batching. The **gateway is trusted** to unwrap. Garlic never carries CAM. Gemini never commands the radio.

---

## 1. Entire problem statement

### 1.1 Setting

A corridor of vehicles uses C-V2X. The RSU in this paper is a **relay / edge box**: it (i) participates in safety traffic (hears and/or forwards CAM/BSM, occasional DENM), (ii) terminates or forwards IP/flow traffic on the ITS **Uu / backhaul**, and (iii) must notify an operator when it is under flood. Compute and radio are **shared** between (i) and (ii). It is not a data-center IDS and not a full gNB.

Let time be slotted in two clocks, never mixed:

- **Safety clock** \(t\): milliseconds (CAM period, C-V2X subframe).
- **Report clock** \(n\): seconds (incident tickets, overlay hops, Gemini).

### 1.2 Two-plane threat

An adversary \(\mathcal{A}\) can do **at least one** of the following. The paper treats them as **coupled**.

**Plane A — radio / safety (availability of CAM).**  
\(\mathcal{A}\) injects RSU-bound or backhaul-bound flows whose **labels come from the LR-HR DDoS 2024 SDN CSV** (Section 9): \(\mathrm{Label}=0\) normal, \(\mathrm{Label}=1\) malicious (low-rate and high-rate mixed in one class). Those flows compete with CAM **on this box** (Section 1.3). Effect on the air is **only** through the coupling model in Section 1.4, not a hidden 3GPP stack:

- channel busy ratio \(\mathrm{CBR}_t\) rises if the radio scheduler is shared,
- legitimate CAM \(\mathrm{PRR}_t\) falls,
- \(\mathrm{AoI}_t\) of safety state grows.

A classifier that is accurate **after** the PCAP is closed does not restore \(\mathrm{PRR}_t\). The RSU must **detect on-box** and **act on-box** inside the safety clock.

**Plane B — management / identity (availability and privacy of the incident).**  
Separate adversary and observations: Section 5. If the RSU opens one clear session (plain HTTPS to Gemini or a SOC):

- a **link observer** maps which RSU raised the alarm,
- \(\mathcal{A}\) **cuts** that path so the operator is blind while CAM is already dying,
- the ticket leaks a network identifier that safety standards try not to put in the clear.

**Problem (one sentence).** Under a flood, keep CAM alive on the air without waiting for the cloud, and still deliver an operator-grade incident without handing a **link-level observer** a named RSU on a single path — without claiming anonymity from the **trusted gateway**.

Plane A is TinyML + local mitigate. Plane B is **garlic routing of incident cloves** (bundling + cover, not merely extra hops). Gemini consumes cloves **after** gateway unwrap; it is not a hop on the safety clock.

### 1.3 Why a backhaul / RSU-bound flood hurts C-V2X reception

A flood on the ITS backhaul degrades CAM **only if** CAM and that traffic **share a bottleneck on the RSU**. This paper’s RSU is a **relay with a shared bottleneck**, not an independent radio plus an independent Linux router.

**Primary mechanism (always on in Block B):** shared **CPU / packet pipeline**. RX interrupt, flow table, TinyML preprocess, and CAM decode/forward share one compute budget. Offered flood load \(\lambda_t\) raises utilization \(\rho_t\). CAM frames that miss their processing deadline are dropped in software even if the air was free. That is enough to move PRR and AoI.

**Secondary mechanism (on when \(\beta>0\)):** shared **scheduler**. Uu backhaul and PC5/C-V2X share occupancy; flood bytes raise CBR. The only occupancy knobs are the two non-`none` actions in Section 1.5: **rate-limit** or **quarantine** flows that D labeled malicious, which lowers attack intensity \(\lambda^{\mathrm{att}}\) **and can drop benign bytes** (collateral, Section 1.4). If the radio is partitioned, set \(\beta=0\) and keep CPU coupling only — do not fake a CBR win.

**Not claimed:** the DDoS dataset *is* NR-V2X IQ, or that every RSU in the field shares Uu and PC5. Claimed: *this* evaluation RSU shares CPU always, radio optionally, and the actuator is motivated by those bottlenecks.

### 1.4 Coupling model (Plane A numbers come from here)

Block B is a **stated parametric coupling**, not a 3GPP PHY/MAC. A ranking `no-defense < detect-only < TinyML+act < oracle` that only reduces attack \(\lambda\) is **vacuous** (PRR monotone in \(\lambda^{\mathrm{att}}\)). The ranking that can **flip** is **TinyML+act vs detect-only**, once false-positive actions have a **collateral cost**.

**Slot construction (no timestamps in the CSV).** Each row is one flow. Slot \(t\) is a batch of \(B\) consecutive replayed flows (default \(B=32\) after unique-row split). Let \(b^{\mathrm{att}}\) / \(b^{\mathrm{ben}}\) be attack / benign **byte_count** in the batch (true labels). Normalized attack intensity \(\lambda^{\mathrm{att}}_t = b^{\mathrm{att}} / (b^{\mathrm{att}}+b^{\mathrm{ben}}+\varepsilon) \in [0,1]\).

**Actuator effect on bytes (this is where FPs hurt).** For each flow, M applies \(a \in \{\mathrm{none},\,\mathrm{rl},\,\mathrm{q}\}\) from Section 1.5. Keep fractions: \(\eta(\mathrm{none})=1\), \(0 < \eta(\mathrm{rl}) < 1\), \(\eta(\mathrm{q})=0\) (drop). After action:

- \(\lambda^{\mathrm{att,eff}}_t\): surviving **attack** byte share (true Label 1 after \(\eta(\hat{a})\)).
- \(\chi_t\): **collateral** = benign (Label 0) bytes dropped or rate-limited away, divided by benign bytes offered. \(\chi=0\) if detect-only or \(a=\mathrm{none}\).

**CPU / CBR** (attack load after act; collateral does not reduce attack, it taxes the good class):
\[
\rho_t = \mathrm{clip}\big(\rho_0 + \alpha\,\lambda^{\mathrm{att,eff}}_t,\; 0,\; 1-\varepsilon\big), \qquad
\mathrm{CBR}_t = \mathrm{clip}\big(\mathrm{CBR}_0 + \beta\,\lambda^{\mathrm{att,eff}}_t,\; 0,\; 1\big).
\]

**PRR with collateral** (CAM-adjacent / relayed useful traffic loses share when M punches the wrong flows):
\[
\mathrm{PRR}_t = \underbrace{\exp(-\gamma_{\mathrm{cbr}}\,\mathrm{CBR}_t)\,(1-\rho_t)^{\gamma_{\mathrm{cpu}}}}_{\text{flood physics}} \cdot \underbrace{(1-\nu\,\chi_t)}_{\text{FP tax}}, \qquad
\mathrm{AoI}_t = \frac{T_{\mathrm{CAM}}}{\mathrm{PRR}_t+\varepsilon}.
\]
Report also **benign goodput** \(1-\chi_t\) as a first-class column. Default \(\nu=1\) (full tax on the CAM-adjacent share). Sweep \(\nu \in \{0,0.5,1\}\): \(\nu=0\) recovers the old vacuous ranking; \(\nu>0\) lets TinyML+act **lose to detect-only** when FPR is high or when M quarantines at low \(\sigma\).

**Sensitivity lock (non-vacuous).** Grid \(\{\alpha,\beta,\gamma_{\mathrm{cbr}},\gamma_{\mathrm{cpu}},\nu\}\). We **do not** promise `TinyML+act` always beats detect-only. We promise to **report** where it wins/loses. Oracle should still beat TinyML+act on PRR **and** keep \(\chi\approx 0\).

**Calibration (one measured anchor, cheap).** Replay unique CSV flows plus a CAM-like UDP stream (period \(T_{\mathrm{CAM}}\)) on an **RSU-class CPU** (Raspberry Pi or equivalent). Measure CAM **deadline-miss rate** vs offered attack byte rate. Fit \(\alpha,\gamma_{\mathrm{cpu}}\) to that curve. \(\gamma_{\mathrm{cbr}}\) stays parametric unless a radio testbed exists. Say in the paper: *CPU exponents calibrated; CBR exponent assumed when \(\beta>0\).*

### 1.5 Observables and actions

At slot \(t\) the RSU observes either one flow vector \(\mathbf{x}\) (Block A) or a batch of \(B\) flows (Block B), plus coupling scalars \((\mathrm{CBR}_t, \mathrm{PRR}_t, \mathrm{AoI}_t,\chi_t)\).

**Detector** (TinyML, binary \(C=2\)):
\[
(\hat{y}, \sigma) = f_\theta(\mathbf{x}), \quad \hat{y}\in\{0,1\}, \quad \sigma = 1 - H(\hat{p})/\log 2.
\]

**Actuator map (only these three values; no extra occupancy PHY).**

| \(\hat{y}\) | \(\sigma\) vs \(\tau\) | \(a\) | Byte keep \(\eta\) |
|---|---|---|---|
| 0 (benign) | any | \(\mathrm{none}\) | 1 |
| 1 (malicious) | \(\sigma \ge \tau\) | \(\mathrm{q}\) quarantine | 0 |
| 1 (malicious) | \(\sigma < \tau\) | \(\mathrm{rl}\) mild rate-limit | \(\eta_{\mathrm{rl}}\in(0,1)\) e.g. \(0.5\) |
| anything else (no class in this CSV) | — | \(\mathrm{none}\) | 1 |

There is **no unmapped attack type** in LR-HR 2024 (binary). If a future head emits an unknown class, **fail closed to `none`** (do not quarantine). \(\tau\) is a paper knob: low \(\tau\) quarantines more, raises \(\chi\) on FPs, can make TinyML+act **worse** than detect-only.

**Never** wait for Gemini or a garlic hop.

**Oracle (Block B).** Same coupling **including \(\chi\)**, same table as above, but \(y^\star=\mathrm{Label}\) and \(\sigma=1\) (so Label 1 always \(\mathrm{q}\), Label 0 always \(\mathrm{none}\)). Isolates detector error. Oracle \(\chi=0\) on a clean label replay. The oracle is not a stronger radio.

**Clove** (incident declared, report clock \(n\)):
\[
c_n = \mathrm{Enc}_{\mathrm{gw}}\big(\hat{y},\ \sigma,\ a,\ \mathrm{CBR}^{\mathrm{before/after}},\ \mathrm{PRR},\ \mathrm{id}_{\mathrm{RSU}}^{\mathrm{pseudonym}}\big).
\]
\(\mathrm{Enc}_{\mathrm{gw}}\): only the **trusted gateway** can decrypt (Section 5.1).

**Bulb:** \(B_n = \mathrm{Garlic}(c_n, c'_n, \ldots)\) — real cloves plus **cover cloves**.

**Gateway:** unwrap, **then** optionally Gemini. Gemini never sees the RSU’s routing IP as an identifier.

### 1.6 Objectives (shared audit)

**Safety plane (primary for VTC):**
\[
\max\ \mathbb{E}[\mathrm{PRR}], \quad \min\ \mathbb{E}[\mathrm{AoI}], \quad \text{detect/act latency } \ll T_{\mathrm{CAM}}.
\]
CBR is a witness, and is uninformative when \(\beta=0\).

**Management plane:**
\[
\max\ \Pr(\text{incident reaches gateway}), \quad \min\ \mathrm{AttAcc}(\mathcal{A}_B),
\]
with \(\mathrm{AttAcc}\) defined in Section 5.2, delay on the **report** clock.

**Detector constraint:** size, RAM, **ms/flow** on an RSU-class CPU. **F1 is feasibility for \(f_\theta\)**, not the main KPI.

**LLM constraint:** Gemini wall-clock \(\gg\) TinyML wall-clock.

### 1.7 Intro paragraph

C-V2X relay RSUs share CPU (and sometimes radio) between cooperative awareness and ITS backhaul, so a flow flood is a CAM problem, not only an IDS log. They must also notify an operator without handing a link observer a named box. We train TinyML on **LR-HR DDoS 2024** (SDN flows, binary labels; **not** a C-V2X trace). Existing DDoS models assume a data-center clock and a single URL; extra hops without **bundling** still leak by timing and size. False-positive quarantine **costs benign bytes**, so acting is not monotone-better than detecting. The problem is two-plane: (A) on-box classify + act, audited on a **stated** PRR coupling with **collateral \(\chi\)** and a **CPU calibration**; (B) garlic cloves vs a **pinned** observer game, with **AttAcc vs batch delay**. Gateway trusted. LLM after unwrap only.

---

## 2. Story (slot and ticket)

**On the road.** \(f_\theta\) runs every window; \(\hat{y}=\) benign; \(a_t=\) none; no clove.

**Flood starts.** Shared CPU (and maybe radio) moves \(\rho_t\) and \(\mathrm{PRR}_t\). If D says malicious and \(\sigma\ge\tau\), M **quarantines**; if \(\sigma<\tau\), M **rate-limits**. Attack \(\lambda^{\mathrm{att,eff}}\) falls; if those flows were actually benign, \(\chi\) rises and PRR can **fall**. CAM PRR **and** \(\chi\) are the plots.

**Ticket.** The RSU does **not** POST JSON to Gemini. It packs a clove, batches a bulb (real + cover), garlic-routes to the gateway. Sister RSUs contribute only if **honest and not CPU-dead** (Section 5.3).

**Operator.** Gateway decrypts (it **does** learn the pseudonym). Gemini writes a note. CAM was never in the bulb.

**Uncertain detector.** Low \(\sigma_t\): conservative \(a_t\); no Gemini in the loop.

---

## 3. Permissioned processes vs TinyML (least privilege, not “agentic RAN”)

**Claim in the paper:** clock separation and **least privilege** — who may call \(f_\theta\), who may change \(\lambda^{\mathrm{att,eff}}\) and \(\chi\), who may emit a clove, who may call Gemini. The word **agent** is a shorthand for those processes. D and M are a **fixed pipeline with a rule-based (or frozen) policy**, not a debating LLM swarm. A skeptical reader who sees “IDS + if-then” is **correct about D and M**; the non-trivial split is **permission + two clocks + Plane B tools**.

### 3.1 TinyML is a model. D/M/R are roles with tools.

| | **TinyML \(f_\theta\)** | **Permissioned process (D, M, or R)** |
|---|---|---|
| What | Function: window → class, \(\sigma\). Fixed weights. | Goal, **allowed tools**, typed messages. |
| Memory | Weights + \(\mathbf{x}_t\). | Last class/action, clove-already-sent, CBR trend. |
| Clock | Every safety window. | D, M: ms. R: s. |
| Training | Supervised on the DDoS dataset. | M: rules or small frozen RL. Gemini: prompt only. |
| Authority | Labels only. | M alone may set \(a_t\). R alone may pack garlic. Gateway alone may call Gemini. |

TinyML is the **eyes**. It is **not** a process. Calling the quantized CNN an “agent” is forbidden in drafts.

**D (detector).** Tools: \(f_\theta\) only. Publishes `Detect{y,σ,t}`. No radio, no HTTP.

**M (mitigator).** Tools: `none` / `rl` / `q` only. Subscribes to `Detect`, never to Gemini. Low \(\sigma\) on a malicious vote → `rl`, not Gemini.

**R (reporter).** Tools: clove, bulb, overlay; at gateway, Gemini. Cannot emit `Act`.

### 3.2 Interaction (one-way bus)

```
  x_t, coupling(CBR, PRR)
           │
           ▼
   ┌───────────────┐   Detect{y,σ,t}   ┌───────────────┐
   │  D  (TinyML)  │ ────────────────► │  M  (rules)   │
   └───────────────┘                   └───────┬───────┘
                                               │ Act{a, CBR, t}  committed
                                               ▼
                                       ┌───────────────┐
                                       │  R  (garlic)  │
                                       └───────┬───────┘
                                               │ seconds, bulbs
                                               ▼
                                       Gateway (trusted unwrap) → optional Gemini
```

Downstream cannot command upstream. Gemini **cannot** emit `Act`.

**Forbidden.** Gemini → M. D → Gemini. CAM in a clove. Vehicle → weights.

### 3.3 Why the split (without selling “agents”)

- **Speed:** D+M cannot stall on overlay/Gemini.  
- **Least privilege:** only M may set \(a\in\{\mathrm{none},\mathrm{rl},\mathrm{q}\}\).  
- **Two-plane threat:** M is Plane A; R is Plane B.  
- **Ablation rows:** TinyML only; D+M no report; D+M + HTTPS; D+M + onion no batch; D+M + garlic; +Gemini.  
- **Failure isolation:** wrong class → M default; overlay down → CAM already acted; Gemini wrong → radio unchanged.

**Do not add.** LLM debate before \(a_t\); RAN-wide agent swarm; garlic as a Plane A mitigator.

### 3.4 Paragraph for the paper

We distinguish \(f_\theta\) from **permissioned processes**. The classifier has no tools. D *invokes* \(f_\theta\) and publishes `Detect`. M *consumes* `Detect` and *only M* may set \(a\) (hence \(\lambda^{\mathrm{att,eff}}\) and \(\chi\)). R *consumes* `Act` and *only R* may garlic-route; Gemini is invoked *only after* trusted unwrap. Usefulness is **who may act, how fast, on which plane**, not extra intelligence on the same tensor. D and M are deliberately a pipeline.

---

## 4. TinyML (dataset → RSU)

- Train \(f_\theta\) on the labeled DDoS dataset (true labels; no invented V2X column names).
- Quantize / distill for RSU CPU.
- **Unit:** one CSV **flow** = one TinyML call (24 numeric features + binary label). There are **no timestamps**, so there is no time window \(W\). Block B **batches** \(B\) flows into a slot (default \(B=32\)).
- **ms/flow** = inference on RSU-class CPU (plus trivial feature copy). That is the Block A latency number.
- **Duplicates:** 69{,}530 duplicate rows in the file; **drop duplicates before split** or Block A leaks.
- Honesty: SDN/Mininet/Ryu **flow IDS**, not NR-V2X IQ; radio KPIs from Section 1.4. Label 1 mixes LR and HR; we **do not** claim a 3-class LR vs HR head unless we derive a proxy (e.g. `Flow Pkts/s` / `byte_count` threshold) and say it is **ours**, not the dataset.

---

## 5. Garlic (Plane B) — threat model, trust, baselines

### 5.1 Trust

- **Gateway is trusted** for Plane B: it can decrypt cloves, **learn the pseudonym**, call Gemini, and see incident contents. We **do not** claim anonymity against the gateway. We claim protection against a **non-colluding network observer** \(\mathcal{A}_B\).
- RSUs do **not** hold the Gemini key.
- Pseudonym \(\mathrm{id}^{\mathrm{pseudonym}}\) is an identifier **for the gateway**, not a public name on the wire.

### 5.2 Adversary \(\mathcal{A}_B\) and identifiability (pinned knobs)

\(\mathcal{A}_B\) **does not** control the gateway. It **observes a fraction \(\phi\) of backhaul links** \(L_{\mathrm{obs}}\) (timing, size, next-hop). No plaintext cloves.

**Pinned default (paper table; then curves).** \(N=20\) RSUs. \(\phi \in \{0.2, 0.5, 1.0\}\). Batch window \(T_b \in \{0.5, 1, 2, 5, 10\}\) s. Cover rate \(r_c\) = dummy cloves per real clove, \(r_c \in \{0,1,3,7\}\). **Incidents per epoch** \(m\): number of **real** cloves that may enter one bulb. Default \(m=1\) is the **hard** case (singleton + easy-to-spot cover). Also run \(m \in \{1,2,5\}\). If garlic is only shown at large \(m\) and large \(r_c\), it is dressed-up onion.

**Attribution game.** Each epoch, \(m\) RSUs in \(S\) emit a real clove; others may emit cover. \(\mathcal{A}_B\) names a source for each observed bulb. \(\mathrm{AttAcc}\) = fraction of real incidents correctly named. Chance = \(1/N\) (or \(1/\#\{\text{RSUs that sent any overlay frame}\}\)).

**Plots (mandatory, not one number).** (i) \(\mathrm{AttAcc}\) vs \(T_b\) for each \(r_c\), onion-no-batch as \(T_b\to 0, r_c=0\). (ii) \(\mathrm{AttAcc}\) vs \(r_c\) at fixed \(T_b=2\,\mathrm{s}\). (iii) **Frontier:** added report delay \(\approx T_b/2\) (plus hops) vs \(\mathrm{AttAcc}\) — this **is** garlic’s contribution. Annotate an operator budget, e.g. “ticket within 2 s / 5 s.” HTTPS AttAcc \(\approx 1\) when the Gemini path \(\in L_{\mathrm{obs}}\).

### 5.3 Cover cost, sister RSUs, compromise

- **Cover cloves** cost bytes on a stressed backhaul. Overhead = extra overlay bytes/s vs \(r_c\). Default: cover is **Plane B only** (not added to \(\lambda^{\mathrm{att}}\)). Optional row: shared-CPU tax \(\alpha_{\mathrm{cover}}\).
- **Sister RSUs** contribute cloves only if **up and honest**. If a sister is **also flooded**, it may fail to add a clove; bulbs shrink toward singletons and AttAcc may rise — **report that degradation**.
- If a sister is **compromised**, it can inject **false cloves** (noise or lies). False cloves **must not** change \(a_t\) (Plane A already committed). Gateway may discard inconsistencies; we do **not** claim garlic authenticates the *radio* truth. Optional: gateway rate-limits cloves per pseudonym.

### 5.4 What garlic adds vs cheaper Plane B

Garlic = layered path hiding **plus batching plus cover**. Distinguishing ablation is **onion, no batch, no cover**.

| Plane B method | Path cut | Observer attribution | Extra vs HTTPS |
|---|---|---|---|
| Clear HTTPS to Gemini | Single URL dies | High if path in \(L_{\mathrm{obs}}\) | — |
| Multipath TLS | Better delivery | Endpoints still named | Extra sockets |
| VPN to SOC | Better delivery | Tunnel endpoints named | VPN setup |
| Onion, 3-hop, **no** batch/cover | Better delivery | Singleton timing/size | Hops, no mix |
| **Garlic (onion + batch + cover)** | Better delivery | Target: AttAcc closer to chance | Hops **+ mix bytes** |

Without the onion-no-batch row, garlic looks like “we used Tor.” That row is **mandatory**.

### 5.5 Mechanics to implement (minimal)

1. Clove: encrypt to gateway; no PCAP; no vehicle IDs.  
2. Bulb: \(k \ge 2\) including dummies.  
3. Overlay: \(\ge 2\) next hops.  
4. Gemini only at gateway.

---

## 6. Contributions

1. **Two-plane, two-clock** problem: CAM availability under a **shared-bottleneck relay RSU**, and incident deliverability/unlinkability against a **link observer**, with a **trusted gateway**.
2. TinyML on LR-HR 2024 (unique flows) + local `{none, rl, q}`, audited on coupling **with collateral \(\chi\)** and a **Pi calibration** of \(\alpha,\gamma_{\mathrm{cpu}}\).
3. Garlic as **bundling + cover**, vs HTTPS / MP-TLS / VPN / **onion-no-batch**; **AttAcc curves** over \(T_b,r_c,m\) and the **delay–AttAcc frontier**; cover bytes; sister failure.
4. **Least privilege and clock separation** (D/M pipeline; Gemini after unwrap), not an agentic RAN.

Self-plagiarism guard vs CSLM / TA-CR / ProShift / PassHy: new task, KPIs, \(a_t\), coupling, garlic plane. No factory 5QI, no LEO pass phase, no \((\tau,\Gamma)\) hypernet.

---

## 7. Evaluation

| Block | Question | Numbers |
|---|---|---|
| A | Can TinyML see Label 1 on **unique** flows? | F1, confusion, kB, RAM, **ms/flow** on Pi-class CPU |
| B | Does \(a\) save CAM **after FP tax**? | PRR, AoI, CBR (\(\beta>0\)), **\(\chi\)**; sweep \(\alpha,\beta,\gamma,\nu\); oracle = Label, \(\sigma=1\), same map; **calibrate** \(\alpha,\gamma_{\mathrm{cpu}}\) |
| C | Does garlic hide/deliver the ticket? | Delivery under path cut; AttAcc vs \(T_b,r_c,m\); **delay–AttAcc frontier**; cover bytes; sister down / lie |
| Gemini | Off-path latency (**one row**, not a block) | TinyML ms/flow vs Gemini s/report. Optional: retries under path cut |

**Plane A baselines.** No defense; detect-only (\(a=\mathrm{none}\), \(\chi=0\)); TinyML+act (§1.5); oracle.

**Plane B baselines.** HTTPS; multipath TLS; VPN; onion-no-batch; garlic. Plus garlic, no Gemini.

---

## 8. Non-goals

- Garlic/I2P on CAM. Garlic as the **radio** mitigator.  
- Anonymity **against the gateway**.  
- Gemini as classifier or actuator.  
- Full 5G/Mode 2 stack; O-RAN; “entire 6G agent network.”  
- Relabeling CIC-style features as NR-V2X IQs.  
- Selling D/M as autonomous LLM agents.

---

## 9. Dataset (measured from the local CSV)

**File.** `LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv` (workspace root; Kaggle: abdussalamahmed / *LR-HR DDoS 2024 Dataset for SDN-Based Networks*). SDN/Mininet + Ryu; iPerf normal; Scapy/Hping3 malicious. **Not** C-V2X.

| Field | Value in *this* file |
|---|---|
| Rows × cols | 113{,}407 × 25 (24 features + `Label`) |
| `Label` | **0 = normal** (42{,}899), **1 = malicious** (70{,}508). LR and HR are **not** separate labels |
| Unit | **Flow** (one row). No packet timestamps |
| Time column? | **No.** `flow_duration` exists and can be **negative** (min \(-154\)); do not treat as a clock |
| Duplicates | **69{,}530** duplicate rows. Use **unique** rows for train/val/test (~43.9k) or leak F1 |
| Features (24) | `flow_duration`, `protocol`, `srcport`, `dstport`, `byte_count`, `packet_count`, `Tot Bwd Pkts`, `TotLen Fwd Pkts`, `TotLen Bwd Pkts`, `Fwd Pkt Len Std`, `Flow Pkts/s`, `Fwd/Bwd PSH/URG Flags`, `Fwd/Bwd Header Len`, `Pkt Len Var`, `FIN/SYN/RST Flag Cnt`, `Pkt Size Avg`, `Init Fwd/Bwd Win Byts` |
| TinyML input dim | 24 (drop `Label`; optionally drop constant-ish flags after a variance check) |
| Nulls | 0 |
| Protocols | 0, 1, 6, 17 |
| Cite | Kaggle dataset card (Ahmed); related use e.g. DOI `10.2298/sjee2502183s` (same 113{,}407 / 42{,}899 / 70{,}508 split) |

**Block A split lock.** Deduplicate → stratified split on `Label`. Report F1 on **unique** held-out flows. A 99% F1 on the raw file with duplicates is not a result. After dedup, Label 1 is only **987** rows (raw 70{,}508 were mostly copies).

**Shortcut (must disclose).** On unique rows, **every Label 1 flow has `byte_count = 0`**. `byte_count > 0` ⇒ benign. TinyML/LSTM numbers that ignore this are partly a zero-byte detector. **Do not** put `byte_count` into \(\lambda^{\mathrm{att}}\) (it is identically 0 for attacks). Use **unit flow mass** (or `packet_count`, which is also ~0 on attacks).

**Block B replay lock.** Shuffle unique flows into batches of \(B=32\). \(\lambda^{\mathrm{att}}\) = fraction of Label 1 **flows**, not bytes. Detector sees the 24 features.

**Runner.** `papers/cv2x-rsu-ddos/code/train_block_a.py` (PyTorch TinyMLP, not the leaky Kaggle Keras notebook).

---

## 10. Story lock

A later draft is **wrong** if it: (i) puts CAM in a bulb; (ii) calls garlic the C-V2X defense; (iii) puts Gemini on the safety clock; (iv) reports only F1, or F1 on **undeduplicated** rows; (v) uses a monotone-in-\(\lambda\) ranking without \(\chi\); (vi) omits why backhaul flood hits CAM; (vii) claims unlinkability from the gateway; (viii) omits onion-no-batch; (ix) calls \(f_\theta\) an agent; (x) leaves the oracle or unknown-class map undefined; (xi) reports a single AttAcc with \(m\gg 1\) only; (xii) treats LR-HR 2024 as a C-V2X trace or as timed windows.

**This file:** two planes, two clocks, **collateral coupling**, **Pi calibration**, **pinned AttAcc curves**, SDN flow dataset as labeled.

---

## 11. Reviewer-risk lock (mapped)

| Risk | Where it is answered |
|---|---|
| Vacuous ranking | §1.4 collateral \(\chi\), \(\nu\); TinyML+act can lose to detect-only |
| Unanchored \(\gamma_{\mathrm{cpu}}\) | §1.4 Pi replay calibration of \(\alpha,\gamma_{\mathrm{cpu}}\) |
| AttAcc one number | §5.2 pinned \(N,\phi,T_b,r_c,m\); curves; hard case \(m=1\) |
| Batch vs operator delay | §5.2 and Block C delay–AttAcc frontier |
| Occupancy wording / oracle / unknown class | §1.5 three actions only; unknown → `none`; oracle = Label, \(\sigma=1\) |
| Gemini as a block | §7 one table row (+ optional retries) |
| Dataset empty / no clock | §9 LR-HR 2024 binary SDN flows, duplicates, **no timestamps** |
