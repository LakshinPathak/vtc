"""Block A: TinyML detector on unique LR-HR 2024 flows.

Fixes vs the Kaggle dummy notebook:
  - drop duplicate rows (leak otherwise)
  - stratified split; StandardScaler fit on train only
  - no train-only Gaussian noise (that was a robustness gimmick, not TinyML)
  - LSTM/GRU-on-24-unordered-features is not a sequence model; omitted
  - logistic regression as the tiny linear baseline
  - binary confidence sigma = 1 - H(p)/log 2 for the {none, rl, q} map
  - tau sweep: TinyML+act can raise collateral chi on false positives
  - ms/flow on CPU (RSU-class clock), not only F1
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "LR-HR DDoS 2024 Dataset for SDN-Based Networks.csv"
OUT = ROOT / "results" / "block_a"
PLOT = OUT / "plots"
OUT.mkdir(parents=True, exist_ok=True)
PLOT.mkdir(parents=True, exist_ok=True)

RNG = 42
EPOCHS = 20
BATCH = 256
ETA_RL = 0.5  # byte keep if rate-limit
HIDDEN = (16, 8)


def binary_sigma(p: np.ndarray) -> np.ndarray:
    p = np.clip(p.astype(np.float64), 1e-6, 1.0 - 1e-6)
    h = -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))
    return 1.0 - h / np.log(2.0)


def actuator(y_hat: np.ndarray, sigma: np.ndarray, tau: float) -> np.ndarray:
    """Return eta keep-fraction per flow: 1 none, ETA_RL rl, 0 quarantine."""
    eta = np.ones(len(y_hat), dtype=np.float64)
    mal = y_hat == 1
    eta[mal & (sigma >= tau)] = 0.0
    eta[mal & (sigma < tau)] = ETA_RL
    return eta


def collateral_and_attack_remain(
    y_true: np.ndarray, mass: np.ndarray, eta: np.ndarray
) -> dict:
    """mass: per-flow weight. Do NOT use byte_count: Label 1 bytes are identically 0."""
    y_true = y_true.astype(int)
    ben = y_true == 0
    att = y_true == 1
    m_ben = mass[ben].sum() + 1e-9
    m_att = mass[att].sum() + 1e-9
    chi = float((mass[ben] * (1.0 - eta[ben])).sum() / m_ben)
    att_eff = float((mass[att] * eta[att]).sum() / m_att)
    return {"chi": chi, "attack_remain": att_eff}


class TinyMLP(nn.Module):
    def __init__(self, d_in: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, HIDDEN[0]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(HIDDEN[0], HIDDEN[1]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(HIDDEN[1], 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def load_unique() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv(CSV)
    n_raw = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    feats = [c for c in df.columns if c != "Label"]
    x = df[feats].to_numpy(dtype=np.float64)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    y = df["Label"].astype(int).to_numpy()
    b = df["byte_count"].to_numpy(dtype=np.float64)
    b = np.maximum(b, 0.0)
    meta = {
        "n_raw": n_raw,
        "n_unique": int(len(df)),
        "n_dropped_dupes": int(n_raw - len(df)),
        "label_counts_unique": {int(k): int(v) for k, v in zip(*np.unique(y, return_counts=True))},
        "n_features": len(feats),
        "feature_names": feats,
    }
    (OUT / "dataset_meta.json").write_text(json.dumps(meta, indent=2))
    return x, y, b, feats


def train_mlp(x_tr, y_tr, x_va, y_va, d_in: int) -> TinyMLP:
    device = torch.device("cpu")
    model = TinyMLP(d_in).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()
    tr = torch.utils.data.TensorDataset(
        torch.tensor(x_tr, dtype=torch.float32),
        torch.tensor(y_tr, dtype=torch.float32),
    )
    loader = torch.utils.data.DataLoader(tr, batch_size=BATCH, shuffle=True)
    best_state, best_va = None, -1.0
    history = {"loss": [], "val_acc": []}
    x_va_t = torch.tensor(x_va, dtype=torch.float32)
    y_va_t = torch.tensor(y_va, dtype=torch.float32)
    t0 = time.perf_counter()
    for ep in range(EPOCHS):
        model.train()
        running = 0.0
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            running += float(loss.item()) * len(xb)
        model.eval()
        with torch.no_grad():
            p = torch.sigmoid(model(x_va_t)).numpy()
            acc = float(((p >= 0.5) == (y_va_t.numpy() >= 0.5)).mean())
        history["loss"].append(running / len(tr))
        history["val_acc"].append(acc)
        if acc > best_va:
            best_va = acc
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        print(f"epoch {ep+1:02d} loss={history['loss'][-1]:.4f} val_acc={acc:.4f}")
    train_s = time.perf_counter() - t0
    if best_state:
        model.load_state_dict(best_state)
    model.eval()
    (OUT / "train_history.json").write_text(
        json.dumps({"history": history, "train_seconds": train_s}, indent=2)
    )
    torch.save(model.state_dict(), OUT / "tinyml_mlp.pt")
    return model


def fit_temperature(model: TinyMLP, x_va: np.ndarray, y_va: np.ndarray) -> float:
    """Sharpen poorly scaled logits so sigma can exceed tau."""
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(x_va, dtype=torch.float32))
    y = torch.tensor(y_va, dtype=torch.float32)
    log_t = torch.nn.Parameter(torch.zeros(1))
    opt = torch.optim.LBFGS([log_t], lr=0.25, max_iter=50)
    loss_fn = nn.BCEWithLogitsLoss()

    def closure():
        opt.zero_grad()
        t = torch.exp(log_t)
        loss = loss_fn(logits / t, y)
        loss.backward()
        return loss

    opt.step(closure)
    t = float(torch.exp(log_t.detach()).item())
    return max(t, 1e-3)


@torch.no_grad()
def predict_proba(model: TinyMLP, x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    model.eval()
    t = torch.tensor(x, dtype=torch.float32)
    return torch.sigmoid(model(t) / temperature).numpy()


def ms_per_flow(model: TinyMLP, x: np.ndarray, n_warm: int = 20, n_rep: int = 200) -> float:
    model.eval()
    one = torch.tensor(x[:1], dtype=torch.float32)
    with torch.no_grad():
        for _ in range(n_warm):
            model(one)
        t0 = time.perf_counter()
        for i in range(n_rep):
            model(torch.tensor(x[i % len(x) : i % len(x) + 1], dtype=torch.float32))
        dt = time.perf_counter() - t0
    return 1e3 * dt / n_rep


def eval_scores(y, p, name: str) -> dict:
    yhat = (p >= 0.5).astype(int)
    cm = confusion_matrix(y, yhat).tolist()
    return {
        "name": name,
        "accuracy": float(accuracy_score(y, yhat)),
        "f1": float(f1_score(y, yhat)),
        "roc_auc": float(roc_auc_score(y, p)),
        "confusion": cm,
        "report": classification_report(y, yhat, digits=4),
        "n_params": None,
    }


def plot_confusion(cm, title, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], ["pred 0", "pred 1"])
    ax.set_yticks([0, 1], ["true 0", "true 1"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i][j]), ha="center", va="center", color="black")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    x, y, b, feats = load_unique()
    idx = np.arange(len(y))
    tr_i, te_i = train_test_split(
        idx, test_size=0.2, random_state=RNG, stratify=y
    )
    tr_i, va_i = train_test_split(
        tr_i, test_size=0.2, random_state=RNG, stratify=y[tr_i]
    )
    scaler = StandardScaler()
    x_tr = scaler.fit_transform(x[tr_i])
    x_va = scaler.transform(x[va_i])
    x_te = scaler.transform(x[te_i])
    y_tr, y_va, y_te = y[tr_i], y[va_i], y[te_i]
    b_te = b[te_i]
    # Label-1 byte_count is always 0 in this CSV; coupling mass = one per flow.
    mass_te = np.ones(len(y_te), dtype=np.float64)

    np.savez(
        OUT / "split_scaler.npz",
        mean=scaler.mean_,
        scale=scaler.scale_,
        tr_i=tr_i,
        va_i=va_i,
        te_i=te_i,
    )

    print("unique", len(y), "train", len(y_tr), "val", len(y_va), "test", len(y_te))
    # Shortcut audit: every Label 1 row has byte_count == 0.
    rule_bytes = (x[te_i][:, feats.index("byte_count")] == 0).astype(int)
    rule_pkts = (x[te_i][:, feats.index("packet_count")] == 0).astype(int)
    print(
        "rule byte_count==0  acc",
        float((rule_bytes == y_te).mean()),
        "f1",
        float(f1_score(y_te, rule_bytes)),
    )
    print(
        "rule packet_count==0 acc",
        float((rule_pkts == y_te).mean()),
        "f1",
        float(f1_score(y_te, rule_pkts)),
    )

    print("fitting logistic regression…")
    lr = LogisticRegression(max_iter=500, class_weight="balanced", random_state=RNG)
    lr.fit(x_tr, y_tr)
    p_lr = lr.predict_proba(x_te)[:, 1]
    s_lr = eval_scores(y_te, p_lr, "logreg")
    s_lr["n_params"] = int(lr.coef_.size + 1)
    print(s_lr["report"])

    print("training TinyMLP…")
    mlp = train_mlp(x_tr, y_tr, x_va, y_va, x_tr.shape[1])
    temp = fit_temperature(mlp, x_va, y_va)
    print("temperature", temp)
    p_mlp = predict_proba(mlp, x_te, temperature=temp)
    s_mlp = eval_scores(y_te, p_mlp, "tinyml_mlp")
    s_mlp["temperature"] = temp
    s_mlp["n_params"] = int(sum(p.numel() for p in mlp.parameters()))
    s_mlp["ms_per_flow_cpu"] = ms_per_flow(mlp, x_te)
    print(s_mlp["report"])
    print("params", s_mlp["n_params"], "ms/flow", round(s_mlp["ms_per_flow_cpu"], 4))

    sig = binary_sigma(p_mlp)
    yhat = (p_mlp >= 0.5).astype(int)
    print(
        "p|yhat=1 min/med/max",
        float(p_mlp[yhat == 1].min()) if (yhat == 1).any() else None,
        float(np.median(p_mlp[yhat == 1])) if (yhat == 1).any() else None,
        float(p_mlp[yhat == 1].max()) if (yhat == 1).any() else None,
        "sigma|yhat=1 min/med",
        float(sig[yhat == 1].min()) if (yhat == 1).any() else None,
        float(np.median(sig[yhat == 1])) if (yhat == 1).any() else None,
    )
    taus = [0.1, 0.3, 0.5, 0.7, 0.9]
    sweep = []
    for tau in taus:
        eta = actuator(yhat, sig, tau)
        m = collateral_and_attack_remain(y_te, mass_te, eta)
        n_q = int(((yhat == 1) & (sig >= tau)).sum())
        n_rl = int(((yhat == 1) & (sig < tau)).sum())
        sweep.append(
            {
                "tau": tau,
                "n_quarantine": n_q,
                "n_rate_limit": n_rl,
                "chi_benign_byte_loss": m["chi"],
                "attack_byte_remain": m["attack_remain"],
            }
        )
        print(
            f"tau={tau:.1f} q={n_q} rl={n_rl} chi={m['chi']:.4f} "
            f"att_remain={m['attack_remain']:.4f}"
        )

    detect_only = collateral_and_attack_remain(y_te, mass_te, np.ones(len(y_te)))
    oracle_eta = np.where(y_te == 1, 0.0, 1.0)
    oracle = collateral_and_attack_remain(y_te, mass_te, oracle_eta)

    fpr, tpr, _ = roc_curve(y_te, p_mlp)
    fig, ax = plt.subplots(figsize=(4.5, 4.0))
    ax.plot(fpr, tpr, label=f"TinyMLP AUC={s_mlp['roc_auc']:.3f}")
    fpr2, tpr2, _ = roc_curve(y_te, p_lr)
    ax.plot(fpr2, tpr2, label=f"LogReg AUC={s_lr['roc_auc']:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.legend()
    ax.set_title("Block A ROC (unique flows)")
    fig.tight_layout()
    fig.savefig(PLOT / "roc.png", dpi=140)
    plt.close(fig)

    plot_confusion(s_mlp["confusion"], "TinyMLP", PLOT / "cm_tinyml.png")
    plot_confusion(s_lr["confusion"], "LogReg", PLOT / "cm_logreg.png")

    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    ax.plot([r["tau"] for r in sweep], [r["chi_benign_byte_loss"] for r in sweep], "o-", label=r"$\chi$ (FP tax)")
    ax.plot(
        [r["tau"] for r in sweep],
        [r["attack_byte_remain"] for r in sweep],
        "s-",
        label="attack bytes remaining",
    )
    ax.set_xlabel(r"confidence threshold $\tau$")
    ax.set_ylabel("byte fraction")
    ax.legend()
    ax.set_title("Actuator: collateral vs leftover attack")
    fig.tight_layout()
    fig.savefig(PLOT / "tau_sweep_chi.png", dpi=140)
    plt.close(fig)

    bundle = {
        "logreg": {k: v for k, v in s_lr.items() if k != "report"},
        "tinyml_mlp": {k: v for k, v in s_mlp.items() if k != "report"},
        "logreg_report": s_lr["report"],
        "tinyml_report": s_mlp["report"],
        "tau_sweep": sweep,
        "detect_only": detect_only,
        "oracle": oracle,
        "rule_byte_count_eq_0": {
            "accuracy": float((rule_bytes == y_te).mean()),
            "f1": float(f1_score(y_te, rule_bytes)),
        },
        "rule_packet_count_eq_0": {
            "accuracy": float((rule_pkts == y_te).mean()),
            "f1": float(f1_score(y_te, rule_pkts)),
        },
        "notes": [
            "Duplicates dropped before split. Unique Label 1 is only 987 rows; raw file duplicates attacks.",
            "Scaler fit on train only.",
            "LSTM/GRU omitted: 24 flow stats are not a time sequence.",
            "Label 1 byte_count is identically 0; chi/attack_remain use unit flow mass, not bytes.",
            "sigma = 1 - binary_entropy(p)/log(2); y_hat = 1 iff p>=0.5.",
            "Actuator: y=0 -> none; y=1 and sigma>=tau -> quarantine; else rate-limit.",
        ],
    }
    (OUT / "block_a_metrics.json").write_text(json.dumps(bundle, indent=2))
    print("wrote", OUT / "block_a_metrics.json")


if __name__ == "__main__":
    main()
