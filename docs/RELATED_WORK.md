# IEEE literature for intro / related work (to cite later)

Do **not** dump all of these in 5 pages. Intro ~6–8 cites; related table ~6 rows. Prefer IEEE. Verify DOI on Xplore before the `.bib`.

## Plane A — V2X / RSU DDoS and TinyML

| Cite key (draft) | Venue | Why we cite | Gap vs us |
|---|---|---|---|
| twardokus2023cv2xdos | IEEE TWC, DOI 10.1109/TWC.2023.3249665 | C-V2X sidelink **DoS** on scheduling | Scheduler attack, not flow TinyML + CAM coupling |
| asensio2024zsm | IEEE OJ-VT, DOI 10.1109/OJVT.2024.3375448 | MEC V2X **DDoS**, RSU RL detector, SSLA slices | Cloud/MEC loop; no garlic tickets; not TinyML on LR-HR flows |
| hasan2020v2xsec | IEEE TIV, DOI 10.1109/TIV.2020.2987430 | Survey securing V2X platforms | Survey |
| rsu2022ids | Sensors / RSU online IDS (Ghosh et al. PMC9573621) | RSU IDS + mitigate in VANET | Statistical IDS; no two-clock reporting |
| ccci2025tinyml | IEEE CCCI 2025, DOI 10.1109/CCCI65983.2025.11215096 | TinyML vs LSTM/GRU on **LR-HR DDoS 2024**, ~1 kB, V2X framing | **Closest**: same CSV, Tiny vs LSTM. Likely **no dedup**, no χ actuator, no garlic, treats dataset as V2X. We must cite and separate (unique-row split, byte_count=0 shortcut, CAM coupling) |

## Plane B — onion / garlic in vehicular nets

| Cite key | Venue | Why | Gap |
|---|---|---|---|
| globecom2019i2pvanet | IEEE GLOBECOM, DOI 10.1109/GLOBECOM38437.2019.9013225 | I2P tunnels/garlic **adapted to VANET** | Anonymizes VANET **payload** paths; we forbid garlic on CAM |
| jiot2019onionvanet | IEEE IoTJ, DOI 10.1109/JIOT.2019.2948315 | Mobility-tolerant **onion** for VANET | Onion on vehicle data, not incident mix vs HTTPS |
| nmitcon2023garlic | IEEE NMITCON, DOI 10.1109/NMITCON58196.2023.10276185 | Garlic for IoMV/5G data exchange | Garlic as data plane; we use garlic **only** on tickets |

## SDN / flow DDoS (dataset origin — one cite)

Kaggle LR-HR DDoS 2024 (Ahmed). Optional IEEE-adjacent: SEEE 2025 DOI 10.2298/SJEE2502183S (same 113407/42899/70508 counts). Say **SDN Mininet**, not C-V2X PHY.

## Writing rule

Intro: C-V2X DoS (Twardokus) → MEC/RSU DDoS (Asensio) → TinyML on this CSV (CCCI 2025) **and why F1 is not the paper** → I2P/garlic VANET (GLOBECOM 2019) **on the wrong plane**. Then two-plane contract.
