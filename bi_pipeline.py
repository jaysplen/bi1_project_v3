"""
VacuTech — Analytics pipeline (W1 + W2 + W3).

Unified end-to-end pipeline for inventory rules, repair-duration estimation,
and QA-failure risk. One interpretable algorithm per work package with fixed,
documented hyperparameters. Reads from ``data/`` and writes PNG / CSV / JSON
artefacts into ``exports/``.

Run from the repository root:

    python3 bi_pipeline.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib


def _running_in_notebook() -> bool:
    """True when imported inside Jupyter / IPython (inline plots expected)."""
    try:
        shell = get_ipython().__class__.__name__  # type: ignore[name-defined]
    except NameError:
        return False
    return shell in ("ZMQInteractiveShell", "TerminalInteractiveShell")


if not _running_in_notebook():
    matplotlib.use("Agg")  # headless CLI / CI only

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
EXPORTS = HERE / "exports"
W1_DIR = EXPORTS / "w1"
W2_DIR = EXPORTS / "w2"
W3_DIR = EXPORTS / "w3"
METRICS_PATH = EXPORTS / "metrics_summary.json"

for d in (W1_DIR, W2_DIR, W3_DIR):
    d.mkdir(parents=True, exist_ok=True)

SEED = 7

# ---------------------------------------------------------------------------
# Feature definitions (leakage-safe: intake / pre-QA columns only)
# ---------------------------------------------------------------------------
W2_NUMERIC = ["pump_age_years", "technician_experience_years", "parts_cost_eur"]
W2_CATEGORICAL = [
    "pump_model",
    "complexity_class",
    "failure_type",
    "parts_from_hq_flag",
    "region",
]
W2_TARGET = "repair_duration_days"

W3_NUMERIC = [
    "pump_age_years",
    "technician_experience_years",
    "parts_cost_eur",
]
W3_CATEGORICAL = [
    "pump_model",
    "complexity_class",
    "failure_type",
    "parts_from_hq_flag",
]
W3_TARGET = "qa_failed_flag"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@dataclass
class RawData:
    repairs: pd.DataFrame
    parts_used: pd.DataFrame
    parts: pd.DataFrame


def load_data(data_dir: Path | None = None) -> RawData:
    """Load the three CSVs that this base project depends on."""
    d = Path(data_dir) if data_dir else DATA_DIR
    return RawData(
        repairs=pd.read_csv(d / "repairs.csv"),
        parts_used=pd.read_csv(d / "parts_used.csv"),
        parts=pd.read_csv(d / "parts.csv"),
    )


# ---------------------------------------------------------------------------
# W1 — Inventory optimisation (Apriori association rules)
# ---------------------------------------------------------------------------
def _build_pm_basket(repairs: pd.DataFrame, parts_used: pd.DataFrame) -> pd.DataFrame:
    # Keep all repairs completely independently of whether it is a PM or breakdown job
    scope = parts_used[
        parts_used["kit_part_flag"] == 0
    ].copy()
    basket = (
        scope.groupby(["case_id", "part_id"])["qty"]
        .sum()
        .unstack(fill_value=0)
    )
    return (basket >= 1).astype(bool)


def _plot_w1_top_rules(rules: pd.DataFrame, out: Path) -> None:
    if rules.empty:
        return
    top = rules.sort_values("lift", ascending=False).head(10).copy()
    labels = [f"{a} → {c}" for a, c in zip(top["antecedents"], top["consequents"])]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(range(len(top)), top["lift"], color="#2E5FA1")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Lift")
    ax.set_title("W1 — Top 10 association rules by lift")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def _plot_w1_pareto(basket: pd.DataFrame, out: Path) -> dict:
    counts = basket.sum(axis=0).sort_values(ascending=False)
    cum_share = counts.cumsum() / counts.sum()
    cov80 = int((cum_share <= 0.80).sum()) + 1
    cov90 = int((cum_share <= 0.90).sum()) + 1

    top = counts.head(20)
    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.bar(range(len(top)), top.values, color="#2E5FA1")
    ax1.set_xticks(range(len(top)))
    ax1.set_xticklabels(top.index, rotation=60, ha="right", fontsize=7)
    ax1.set_ylabel("PM cases that needed this add-on part")

    ax2 = ax1.twinx()
    ax2.plot(
        range(len(top)),
        (cum_share.iloc[: len(top)].values) * 100,
        color="#EF4444",
        marker="o",
    )
    ax2.set_ylabel("Cumulative coverage (%)")
    ax2.axhline(80, ls=":", color="grey")

    ax1.set_title(
        f"W1 — Pareto coverage: {cov80} parts ≈ 80% of PM add-on demand "
        f"({cov90} ≈ 90%)"
    )
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return {"cov80": cov80, "cov90": cov90, "unique_parts": int(len(counts))}


def run_w1(raw: RawData) -> dict:
    basket = _build_pm_basket(raw.repairs, raw.parts_used)

    freq = apriori(basket, min_support=0.05, use_colnames=True)
    rules = association_rules(freq, metric="lift", min_threshold=1.2)
    rules = rules.sort_values(["lift", "confidence"], ascending=[False, False])

    rules = rules.assign(
        antecedents=rules["antecedents"].apply(lambda s: ", ".join(sorted(s))),
        consequents=rules["consequents"].apply(lambda s: ", ".join(sorted(s))),
    )
    rules.to_csv(W1_DIR / "w1_rules.csv", index=False)

    _plot_w1_top_rules(rules, W1_DIR / "w1_top_rules.png")
    pareto_stats = _plot_w1_pareto(basket, W1_DIR / "w1_pareto.png")

    metrics = {
        "pm_cases": int(basket.shape[0]),
        "unique_additional_parts": pareto_stats["unique_parts"],
        "rules_count": int(len(rules)),
        "top_lift": float(rules["lift"].iloc[0]) if not rules.empty else 0.0,
        "top_confidence": float(rules["confidence"].iloc[0]) if not rules.empty else 0.0,
        "pareto_cov80_parts": pareto_stats["cov80"],
        "pareto_cov90_parts": pareto_stats["cov90"],
        "method": "Apriori (mlxtend)",
        "min_support": 0.05,
        "min_lift": 1.2,
    }
    with (W1_DIR / "w1_metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)
    return metrics


# ---------------------------------------------------------------------------
# Shared encoder for W2 / W3 — simple, no pipeline, no scaler
# ---------------------------------------------------------------------------
def _encode_xy(
    df: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
    target: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Drop rows with any null in the chosen columns, then one-hot encode categoricals."""
    cols = numeric + categorical + [target]
    use = df[cols].dropna().copy()
    X_num = use[numeric].astype(float)
    X_cat = pd.get_dummies(use[categorical].astype(str), prefix=categorical)
    X = pd.concat([X_num, X_cat], axis=1)
    y = use[target]
    return X, y


# ---------------------------------------------------------------------------
# W2 — Repair-duration regression (Decision Tree)
# ---------------------------------------------------------------------------
def _plot_actual_vs_pred(y_true, y_pred, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_true, y_pred, alpha=0.5, color="#2E5FA1", s=18)
    lo = float(min(np.min(y_true), np.min(y_pred)))
    hi = float(max(np.max(y_true), np.max(y_pred)))
    ax.plot([lo, hi], [lo, hi], "--", color="grey", label="Actual = Predicted")
    ax.set_xlabel("Actual repair duration (days)")
    ax.set_ylabel("Predicted repair duration (days)")
    ax.set_title("W2 — Actual vs predicted (test set)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def _plot_feature_importance(
    importances, feature_names, out: Path, title: str, top: int = 10
) -> None:
    order = np.argsort(importances)[::-1][:top]
    names = [feature_names[i] for i in order]
    vals = [importances[i] for i in order]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(range(len(names)), vals, color="#22C55E")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Feature importance")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def run_w2(raw: RawData) -> dict:
    df = raw.repairs.dropna(subset=[W2_TARGET]).copy()
    X, y = _encode_xy(df, W2_NUMERIC, W2_CATEGORICAL, W2_TARGET)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED
    )

    model = DecisionTreeRegressor(max_depth=6, min_samples_leaf=20, random_state=SEED)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    preds = X_test.copy()
    preds["Actual"] = y_test.values
    preds["Predicted"] = y_pred
    preds.to_csv(W2_DIR / "w2_predictions.csv", index=False)

    _plot_actual_vs_pred(y_test.values, y_pred, W2_DIR / "w2_actual_vs_pred.png")
    _plot_feature_importance(
        model.feature_importances_,
        list(X.columns),
        W2_DIR / "w2_feature_importance.png",
        title="W2 — Decision-tree feature importance (top 10)",
    )

    metrics = {
        "method": "DecisionTreeRegressor (max_depth=6, min_samples_leaf=20)",
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
    }
    with (W2_DIR / "w2_metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)
    return metrics


# ---------------------------------------------------------------------------
# W3 — QA-failure classification (Decision Tree, fixed threshold)
# ---------------------------------------------------------------------------
def _plot_confusion_matrix(cm, out: Path, threshold: float) -> None:
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Pred 0", "Pred 1"])
    ax.set_yticklabels(["Actual 0", "Actual 1"])
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, str(int(cm[i, j])),
                ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black",
                fontsize=13,
            )
    ax.set_title(f"W3 — Confusion matrix at threshold = {threshold:.2f}")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def run_w3(raw: RawData, threshold: float = 0.30) -> dict:
    df = raw.repairs.dropna(subset=[W3_TARGET]).copy()
    X, y = _encode_xy(df, W3_NUMERIC, W3_CATEGORICAL, W3_TARGET)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    model = DecisionTreeClassifier(max_depth=6, min_samples_leaf=20, random_state=SEED)
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    y_pred = (proba >= threshold).astype(int)

    cm = confusion_matrix(y_test, y_pred)
    rec = recall_score(y_test, y_pred, zero_division=0)
    prec = precision_score(y_test, y_pred, zero_division=0)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    preds = X_test.copy()
    preds["actual_failure"] = y_test.values
    preds["predicted_risk_prob"] = proba
    preds["predicted_label"] = y_pred
    preds.to_csv(W3_DIR / "w3_predictions.csv", index=False)

    _plot_confusion_matrix(cm, W3_DIR / "w3_confusion_matrix.png", threshold)
    _plot_feature_importance(
        model.feature_importances_,
        list(X.columns),
        W3_DIR / "w3_feature_importance.png",
        title="W3 — Decision-tree feature importance (top 10)",
    )

    metrics = {
        "method": "DecisionTreeClassifier (max_depth=6, min_samples_leaf=20)",
        "threshold": float(threshold),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "recall_failure": float(rec),
        "precision_failure": float(prec),
        "accuracy": float(report["accuracy"]),
        "class_balance_train_positive": float(y_train.mean()),
    }
    with (W3_DIR / "w3_metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)
    return metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("Loading data ...")
    raw = load_data()
    print(f"  repairs:    {len(raw.repairs)} rows")
    print(f"  parts_used: {len(raw.parts_used)} rows")
    print(f"  parts:      {len(raw.parts)} rows")

    print("\nW1 — Inventory optimisation (Apriori) ...")
    m1 = run_w1(raw)
    print(
        f"  PM cases: {m1['pm_cases']} | rules: {m1['rules_count']} | "
        f"top lift: {m1['top_lift']:.2f}"
    )
    print(
        f"  Pareto: {m1['pareto_cov80_parts']} parts ≈ 80% / "
        f"{m1['pareto_cov90_parts']} ≈ 90%"
    )

    print("\nW2 — Repair duration (Decision Tree regression) ...")
    m2 = run_w2(raw)
    print(
        f"  R² = {m2['r2']:.4f} | MAE = {m2['mae']:.4f} days | "
        f"RMSE = {m2['rmse']:.4f}"
    )

    print("\nW3 — QA-failure risk (Decision Tree classification) ...")
    m3 = run_w3(raw)
    print(
        f"  threshold = {m3['threshold']:.2f} | recall = {m3['recall_failure']:.3f} | "
        f"precision = {m3['precision_failure']:.3f} | accuracy = {m3['accuracy']:.3f}"
    )

    summary = {"w1": m1, "w2": m2, "w3": m3}
    with METRICS_PATH.open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nMetrics summary written to {METRICS_PATH.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
