# Dataset

Place the public CSV here (not committed; ~8 MB):

`LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv`

Source: [Kaggle — LR-HR DDoS 2024 for SDN-based networks](https://www.kaggle.com/datasets/abdussalamahmed/lr-hr-ddos-2024-dataset-for-sdn-based-networks).

`train_block_a.py` reads `vtc/data/` with that filename.

## Split used here

1. Drop exact duplicate rows: 113,407 → **43,877** unique (69,530 dropped).
2. Stratified 80/20 train/test, then 80/20 of the train pool for train/val (seed **42**).
3. `StandardScaler` fit on **train only**.
4. Binary labels: 0 = benign, 1 = attack (low-rate and high-rate in one class).
5. Test size 8,776 with **197** attacks.

Label-1 rows in this CSV have `byte_count` identically zero, so Block A collateral uses **per-flow mass = 1**, not byte_count. See the comment in `train_block_a.py`.

Do not commit the CSV.
