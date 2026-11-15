# Paper 2 plan — Fed-TinySync

**Status.** Plan only. No manuscript, no rewrite of TinyGuard `vtc/manuscript/main.tex`, no training until this file is approved.

**Working title.** Fed-TinySync: Federated TinyML and Garlic-Routed Model Updates at Multi-RSU Edges.

**Venue / track.** IEEE VTC-style. **AI4C** (TinyML / FedAvg) primary. Upload mixing is a **SAQ-shaped section** (classical mixnet + DDoS FL). The SAQ *quantum communications* half of that track is **not** this paper. See §16. Not PHY, WOS, CMA, NVS.

**Code later (not now).** `vtc/code/train_fed.py`, `vtc/code/sim_plane_u_garlic.py`, `vtc/code/plot_paper2.py`, results in `vtc/results/paper2/`. Do not overwrite Paper 1 `block_a_metrics.json`.

---

## 0. Paper 1 vs Paper 2 (do not mix)

| | Paper 1 — RSU-TinyGuard | Paper 2 — Fed-TinySync (this plan) |
|---|---|---|
| How many RSUs | One relay box | \(K\) simulated RSUs (\(5,10,20\)) |
| What we hide | The **incident ticket** (who raised the alarm) | The **weight upload** (who trained tonight) |
| What we train | One TinyML on all unique rows (pooled) | Local shards + FedAvg; pooled is only the **upper bound** |
| Garlic payload | Encrypted clove: \(\hat y,\sigma,a,\mathrm{CBR},\mathrm{PRR}\), no CAM | Flattened TinyML weights (~2.2 KB), no CAM, no ticket |
| Clock for ML | Infer and act in \(\sim 0.10\) ms | Infer in \(\sim 0.10\) ms; **FedAvg only at night** |
| CAM PRR / \(\chi\) | First-class coupling | Cited from Paper 1, **not** the claim |
| LLM / Gemini | Off-path, unscored | **Out of Paper 2** |
| BB84 / Qiskit / QKD | Not in Paper 1 | **Out of Paper 2 v1** (see §16). Confidentiality of the clove stays classical `Enc_gw` |

TinyGuard stays one Overleaf project. Fed-TinySync is a second paper. Same CSV family, different question.

---

## 1. Actual problem (plain language)

A road has **many** cheap roadside units, not one lab PC. Each sees some ITS / backhaul **flows**. Some flows are a flood (DDoS). We want every box to run the **same tiny detector** (TinyML: \(16\)-\(8\)-\(1\), about \(545\) weights, less than a millisecond per flow).

The operator’s problem is no longer “can we get a good \(F_1\) if we pile every unique row on one machine?” Paper 1 already did that (attack-class \(F_1\) near \(0.963\) after dropping duplicates). The new problems are:

1. **Flows must not leave the box.** Policy, volume, and the raw LR-HR file is full of **exact duplicate** rows. Training on the raw table makes accuracy look like \(99\%\) and is a leak. Shipping the CSV to a cloud is exactly that pile.
2. **Each box only sees a piece of the truth.** One stretch of road may see almost all attacks. Another may see almost none. A model trained only locally can be blind on the global test.
3. **Clear uploads name the box.** If every night each RSU posts weights over one HTTPS path, a wiretapper learns **which RSU took part in this round**. That is a live map of the edge, even if they never see a flow.

So Paper 2 solves two coupled failures, **neither of which is CAM**:

- learn a shared tiny detector **without pooling flows**;
- mix **who uploaded the update**, without putting CAM or the Paper 1 ticket in the bulb.

**One sentence.** Federate the detector without shipping flows, and mix who uploaded the update, without touching CAM.

---

## 2. What we are not solving (say in the paper)

- Not restoring CAM PRR by FedAvg.
- Not putting CAM, or Paper 1’s \((\hat y,\sigma,a)\), in a garlic bulb.
- Not waiting for a FedAvg round before the box rate-limits a flood (that stays millisecond and **local**, frozen weights).
- Not claiming garlic stops a **poisoned sister**. Garlic hides *who sent* the packet. Poison is a **median / trimmed-mean** problem. The aggregator is **trusted to unwrap**.
- Not beating \(0.963\) attack \(F_1\) as the trophy. That number is “everyone’s unique train in one pile.” It is the **ceiling**.
- Not \(K\) hardware RSUs, not I2P/Tor in the field, not 3GPP Mode 2, not Gemini.
- Not the Kaggle federated notebook (see §12).

---

## 3. Application and day / night flow

**Setting.** Highway / C-V2X corridor. Relay RSUs share CPU with safety traffic in the **real world**, but this paper’s **measured** objects are unique SDN flows (LR-HR 2024) and a Monte Carlo **upload** observer. Clients in code are **simulated RSUs**. The abstract must say that.

**Day (safety, local, fast)**

```
flow x  -->  frozen TinyML f_theta  -->  (yhat, sigma)  -->  local act if the operator still uses Paper 1
                 ^
                 |  last night's global weights, already on the box
```

No cloud, no FedAvg, no garlic on this path.

**Night (training, slow, many boxes)**

```
each RSU:  train a few epochs on ITS OWN unique flows only
           do not send flows
           send WEIGHTS (~545 floats)  --garlic or onion-->  trusted aggregator
           aggregator: FedAvg or median
           send GLOBAL TinyML back to boxes
```

**On the path to the aggregator**

| Path | What happens | Who is named |
|---|---|---|
| HTTPS | One clear upload | Observer names the RSU with chance \(\phi\) |
| Onion, no batch | Extra hops, one clove, no mix | Delivery can rise; a **seen entry still names** the source |
| Garlic | Wait \(T_b\), cover \(r_c\), several cloves in one bulb | Observer sees a **set**; AttAcc drops only if \(\lvert\mathcal{U}\rvert>1\) |

Onion-without-batching is the **control** that isolates mixing from extra hops. Same logic as Paper 1, **new payload** (weights, not tickets).

**ASCII of the whole paper**

```
each RSU:  flows  -->  TinyML (ms)  -->  local inference (frozen)
                 \
                  \ night: train locally
                   --> WEIGHTS -- HTTPS / onion / garlic --> trusted averager
                   <-- new global TinyML -------------------
```

---

## 4. Two planes (Paper 2 names)

| Plane | Object that moves | Clock | Adversary | Score |
|---|---|---|---|---|
| **M — model** | \(545\)-param weights | minutes / FedAvg rounds | honest clients, or \(n_{\mathrm{bad}}\) poison sisters | attack-class \(F_1\) on a **frozen unique test** |
| **U — upload** | garlic bulb of the **weights** | seconds per round | link observer, fraction \(\phi\) of **update** edges; does **not** control the aggregator | AttAcc vs extra delay, cover bytes, delivery under path cut |

Least privilege: inference does not wait for Plane U. Plane U cannot change yesterday’s frozen \(f_\theta\) until the round **finishes** and the box **installs** the new weights (next day). Aggregator unwraps; we do **not** claim anonymity from the aggregator.

---

## 5. What “strong results” means (honest)

A strong Paper 2 is **anti-leak** and has a ranking that can **flip**. Beating pooled TinyML is **not** required.

All of these must hold:

1. Duplicates dropped **before** any client cut. Scaler never sees the test set. Attack \(F_1\) is the headline. Accuracy is a footnote (benign majority).
2. Pooled TinyML (**P**) sits in the **same table** as the upper bound.
3. FedAvg on **IID unique** shards (**F-IID**) is close to **P** (target gap \(\le 0.03\) attack \(F_1\)) **or** we publish the miss and why.
4. **Attack-skew** (**F-SK**): most unique Label-1 train rows on \(1\)–\(2\) clients. FedAvg **loses** to **P**. That drop is a result.
5. **Local (L)**: mean \(\pm\) std attack \(F_1\) of per-RSU models on the **same** global test.
6. Garlic vs onion vs HTTPS is on **update** paths, new Monte Carlo, payload = weight bytes. HTTPS and onion AttAcc \(\approx\phi\) without mix. Garlic AttAcc falls only when \(\lvert\mathcal{U}\rvert>1\).
7. Poison: \(n_{\mathrm{bad}}\in\{0,1,2\}\). FedAvg \(F_1\) drops. **Median** is the defense. Garlic is **not** the defense.
8. If any run “wins” only with raw-file duplicates, **delete the run**.

---

## 6. Data contract (non-negotiable)

Source: `vtc/data/LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv`.

| Fact | Number |
|---|---|
| Raw rows | \(113{,}407\) |
| Exact duplicates dropped | \(69{,}530\) |
| Unique rows | \(43{,}877\) (\(42{,}890\) benign, \(987\) attack) |
| Unique split, seed \(42\), stratified | train \(28{,}080\) / val \(7{,}021\) / test \(8{,}776\) |
| Features | \(24\); Label 1 `byte_count` \(\equiv 0\) |
| Model | \(16\)-\(8\)-\(1\) MLP, \(\approx 545\) params, CPU, BCE, no LSTM, no Keras, no temperature unless we report \(F_1=0\) |

**Order of operations**

1. Drop duplicates.
2. Split unique rows into train / val / test. Freeze test.
3. Fit scaler on **train only**.
4. **Then** partition **train** into \(K\) clients (`iid` / `skew` / optional `dirichlet`).
5. Never put test rows in a client. Never federate bytes as mass.

Clients = simulated RSUs. Per-client Label-1 **counts** go in Table T1 so a reviewer can see skew.

---

## 7. Methods we compare (locked)

### 7.1 Plane M — detector / FL

| ID | Method | Meaning |
|---|---|---|
| **L** | Local TinyML | Each shard trains alone; each model scored on **global test**; mean \(\pm\) std attack \(F_1\) |
| **P** | Pooled TinyML | All unique train (Paper 1-style upper bound) |
| **F-IID** | FedAvg, IID | Stratified unique train across \(K\) |
| **F-SK** | FedAvg, attack-skew | Most Label-1 train rows on \(1\) or \(2\) clients |
| **F-DIR** | FedAvg, Dirichlet | \(\alpha\in\{0.5,0.1\}\), only if SK is too crude |
| **MED** | Median aggregator | Same shards as F-SK (and poison runs); coordinate-wise median |
| **TM** | Trimmed-mean \(10\%\) | Optional if MED is enough |

**Not in v1:** FedProx, SCAFFOLD, DP-SGD, HE, Flower on devices, LSTM, Gemini.

**Knobs (pilot may change, then freeze).** \(K\in\{5,10,20\}\). Rounds \(R=20\). Local epochs \(E=2\). Batch \(256\). Adam \(10^{-3}\). Participation \(C=1\) main table; one ablation \(C=0.5\). Class imbalance: use `BCEWithLogitsLoss` **pos_weight** from train Label-1 rate if F-IID collapses to all-benign.

**Poison (Plane M).** \(n_{\mathrm{bad}}\in\{0,1,2\}\): label-flip on local Label-1, or Gaussian noise on uploaded weights. Aggregator trusted. Garlic does not see this.

### 7.2 Plane U — upload / mix

Payload = state-dict (~545 \(\times\) 4 B \(\approx 2.2\) KB) + header. Not CAM. Not Paper 1 clove.

| ID | Path | Mix | Hops |
|---|---|---|---|
| **H** | HTTPS, one named path | no | 1 |
| **O** | Onion, no batch, \(r_c=0\), \(T_b\to 0\) | no | \(h\ge 2\) |
| **G** | Garlic, \(r_c\in\{0,1,3,7\}\), \(T_b\in\{0.5,2,5,10\}\) s | yes | same \(h\) as O for a fair hop control |
| **V** | VPN / MP-TLS | **omit AttAcc claims** unless we specify a real model (Paper 1 used hand numbers) |

Observer: \(\phi=0.5\) of **update** entry edges. \(N=K\). Chance \(1/K\). Caption must say: Monte Carlo, not I2P; payload = weights.

AttAcc (same structure as Paper 1, new \(N\) and payload):

\[
\mathrm{AttAcc}=\phi\,\mathbb{E}[1/\lvert\mathcal{U}\rvert]+(1-\phi)/N,\qquad
\mathrm{Deliv}=1-p_{\mathrm{cut}}^{h}.
\]

---

## 8. Plots and tables (camera-ready)

IEEE two-column bars/lines. **No** accuracy-vs-round hero plot (that is the Kaggle notebook).

| Fig | Type | Content |
|---|---|---|
| 1 | line | Attack \(F_1\) vs round: **P** as hline, F-IID, F-SK, L mean |
| 2 | grouped bar | Final attack \(F_1\): L, P, F-IID, F-SK, MED at \(K=10\) |
| 3 | line | Attack \(F_1\) vs \(K\) for F-IID and F-SK |
| 4 | line | Communication bytes (updates \(\times\) rounds \(\times(1+r_c)\)) vs \(F_1\) |
| 5 | line | AttAcc vs \(T_b\) for each \(r_c\) (Plane U) |
| 6 | bar | Delivery under path cut vs AttAcc: H, O, G |
| 7 | line | Attack \(F_1\) vs \(n_{\mathrm{bad}}\) for FedAvg vs MED |
| 8 | optional | Confusion or PR on global test: P vs F-IID vs F-SK |

**Tables**

- **T1.** Unique split + **per-client Label-1 counts** (IID vs SK). Kills leakage and “fake federation” attacks.
- **T2.** Main ML: acc (footnote), attack \(F_1\), params, \(R\), \(E\), bytes.
- **T3.** Plane U: AttAcc, delay \(T_b/2\), cover, \(N,\phi\), payload size in the caption.

---

## 9. Contributions (what the intro will list)

1. **Problem.** Multi-RSU TinyML without a central CSV, with a separate upload-identity threat (not Paper 1’s ticket threat).
2. **Plane M.** Unique-row, train-only scaler, frozen test: Local vs Pooled vs FedAvg-IID vs FedAvg-skew vs Median, attack \(F_1\).
3. **Plane U.** Garlic vs onion-without-batch vs HTTPS on **weight** bulbs. Mixing is the claim, not hops.
4. **Poison.** FedAvg vs Median; garlic explicitly **not** the poison defense.

---

## 10. Intro spine (section order when we write)

1. Many RSUs, cannot centralize the CSV (policy + duplicate leak).
2. TinyML is small enough to federate (\(545\) params). Daytime inference stays on-box.
3. IID unique FedAvg should approach pooled; attack-skew should not. That is the ML claim.
4. A clear HTTPS update still **names** the RSU. Garlic the **update**; onion-without-batch is the control. That is the security claim.
5. A poisoned sister hurts the average; median is the defense; garlic is not.
6. Related work table: CCCI (TinyML on raw CSV), TinyGuard (tickets, not weights), I2P/garlic VANET (payloads, not updates), FedAvg in ITS/FL surveys.

---

## 11. Implementation order (after approval)

1. Shared unique load + frozen split (same as `train_block_a.py`).
2. `partition_clients(..., mode=iid|skew)`.
3. `train_fed.py` → `vtc/results/paper2/fl_metrics.json` (L, P, F-IID, F-SK, MED).
4. **Pilot gate** before garlic: \(K=5\), \(R=5\), F-IID vs P vs L.
5. `sim_plane_u_garlic.py` → `paper2/plane_u.json` (payload = weight bytes).
6. `plot_paper2.py` Figs 1–7.
7. Then, and only then, `vtc/manuscript_paper2/` IEEEtran.

---

## 12. Why the Kaggle federated script is not this paper

That notebook: scaler on **all** rows; **no** duplicate drop; `array_split` of leaked train into 3 clients; `log_loss` on **hard** \(0/1\); client F1 on **training** rows; accuracy as the main plot; 3–4 rounds; Keras dropout copy of TinyML; no frozen unique test; no onion/garlic; no poison; no attack-class headline.

We do not “tweak and paste” it. We replace it with §6–§8.

---

## 13. Go / no-go after the pilot

| Pilot outcome | Decision |
|---|---|
| F-IID attack \(F_1\) within \(\sim 0.03\) of P; later F-SK clearly worse | **Write Paper 2** |
| F-IID \(\approx\) F-SK \(\approx\) P because duplicates leaked into clients | **Stop**, fix partition |
| F-IID attack \(F_1 \approx 0\) (all-benign) | **Stop**, pos_weight / local epochs; **no garlic yet** |
| Only garlic plots, empty FL table | **Do not submit** (TinyGuard with a new caption) |

---

## 14. Explicit non-goals (checklist)

- [ ] No CAM in a bulb
- [ ] No FedAvg inside the rate-limit / quarantine map
- [ ] No “federated garlic restores PRR”
- [ ] No LLM / Gemini
- [ ] No claim of \(K\) hardware RSUs
- [ ] No MP-TLS/VPN AttAcc unless a real model replaces Paper 1’s hand bars
- [ ] No Keras Kaggle script
- [ ] No overwrite of Paper 1 results JSON
- [ ] No merging Paper 1 and Paper 2 Overleaf
- [ ] No BB84, Qiskit, QKD, or “quantum encryption” in Paper 2 v1 (§16)

---

## 15. Approval before code

Confirm all four:

1. Scenario is FedAvg on **unique shards** + garlic on **weight updates**, not “FL inside TinyGuard.”
2. Success is the **full comparison** (P, L, F-IID, F-SK, MED, H/O/G, poison), not beating \(0.963\).
3. \(K\in\{5,10,20\}\), Figs 1–7, Tables T1–T3.
4. Paper 1 `vtc/manuscript/main.tex` stays untouched.

After “yes,” implementation starts at §11 step 1. Not Overleaf first. Not Qiskit first.

---

## 16. Quantum / BB84 / Qiskit (planning thought, then lock)

This section was written **after** splitting the threat, not after picking a library.

### 16.1 Three jobs (think this before any crypto)

The night upload can fail in three different ways. They need three different tools.

| Job | Question | Tool that actually answers it |
|---|---|---|
| **A. Who spoke?** | Can a tapper name which RSU sent tonight’s update? | Garlic mix vs onion-without-batch vs HTTPS. Score: **AttAcc**. |
| **B. Can they read it?** | Can a tapper recover the **bits** of the weights? | `Enc_gw` (classical). Later: AES, or PQC KEM, or (if a quantum **channel** exists) AES under a QKD key. Score: not AttAcc. |
| **C. Are the bits true?** | Can a sister send **wrong** weights under a valid wrap? | Median / trimmed mean, not encryption. Score: attack \(F_1\) vs \(n_{\mathrm{bad}}\). |

BB84 lives only in **B**, and only as **key agreement**, not as the cipher. Garlic lives in **A**. FedAvg poison lives in **C**. Putting Qiskit in Paper 2 does not move Fig 1–3 or Fig 5–6 unless we **lie** and say QKD mixes paths.

BB84 also **assumes** an already-authenticated classical channel. That is circular if the RSU’s problem is an untrusted backhaul observer. Highway RSUs do not have a photon channel in this dataset or in Paper 1’s coupling.

### 16.2 SAQ track name is not a method

“Security Aspects and Quantum Communications” is two rooms. Paper 2 uses the first: mix + FL integrity. The second needs loss, distance, QBER, key rate. A Qiskit H/X/Z demo is a lab tutorial. It will not save an AI4C paper and it can sink one.

### 16.3 Honest crypto ladder (if we ever add **B** later)

1. **Now (Paper 2):** classical `Enc_gw`. Aggregator trusted to unwrap. Same as TinyGuard’s gateway. Enough because AttAcc is about **headers/paths**, not payload bits.
2. **Better classical later, still no Qiskit:** post-quantum KEM (e.g. Kyber) wrapping the 2.2 KB update. This is the honest answer to store-now-decrypt-later on a **classical** backhaul. Still **no** AttAcc change. Could be a short Paper 2 related-work sentence, not a figure.
3. **BB84 / QKD:** only if we name a **physical** quantum link (fiber hut, FSO). Then: QBER vs Eve, sifted key vs dB loss, then AES. QKD is still a **named pair** of endpoints. Garlic still needed for **A**. RSUs stay classical to a gateway; QKD is more plausible **gateway–SOC** than 20 cheap RSUs. No NTN/satellite QKD (PassHy collision, invented stack). Qiskit only **after** that channel model, never inside `train_fed.py`.

### 16.4 Lock for Paper 2 v1

- No BB84, no Qiskit, no “quantum encryption of TinyML,” no quantum figure.
- Optional one-line future work: payload confidentiality is classical; QKD / PQC is out of scope.
- Paper 3, if ever: `vtc/docs/PAPER3_QKD_PLAN.md`, after Paper 2’s unique-split \(F_1\) table exists.

**Decision.** Paper 2 stays Plane **M** + Plane **U**. Job **B** stays `Enc_gw`. Job **A** is garlic. Job **C** is median. BB84 is not a fourth plane.
