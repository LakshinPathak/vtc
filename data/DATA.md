# CSV

Needed by `code/train_block_a.py`:

```
data/LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv
```

Get it from Kaggle (abdussalamahmed / LR-HR DDoS 2024 Dataset for SDN-Based Networks). About 8 MB, gitignored.

After dropping duplicate rows we had 43877 unique (113407 raw). Unique Label 1 is 987. Scaler is fit on train only; arrays/logs under `results/block_a/` are already committed.

Attack rows in the unique set have `byte_count = 0`, so do not use that column as attack intensity.
