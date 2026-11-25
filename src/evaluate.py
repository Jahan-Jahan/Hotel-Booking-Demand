"""Metrics and evaluation plots."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay, accuracy_score, average_precision_score,
    brier_score_loss, f1_score, precision_recall_curve, precision_score,
    recall_score, roc_auc_score, roc_curve,
)

from src.config import FIG_DIR

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})


def best_f1_threshold(y_true, proba) -> float:
    """Threshold that maximises F1 (use on a validation set, never on test)."""
    prec, rec, thr = precision_recall_curve(y_true, proba)
    f1 = 2 * prec[:-1] * rec[:-1] / np.clip(prec[:-1] + rec[:-1], 1e-12, None)
    return float(thr[np.argmax(f1)])


def compute_metrics(y_true, proba, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    return {
        "roc_auc": round(roc_auc_score(y_true, proba), 4),
        "pr_auc": round(average_precision_score(y_true, proba), 4),
        "brier": round(brier_score_loss(y_true, proba), 4),
        "threshold": round(float(threshold), 4),
        "accuracy": round(accuracy_score(y_true, pred), 4),
        "precision": round(precision_score(y_true, pred), 4),
        "recall": round(recall_score(y_true, pred), 4),
        "f1": round(f1_score(y_true, pred), 4),
    }


def _save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, bbox_inches="tight")
    plt.close(fig)


def plot_roc_pr(y_true, probas: dict):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for name, p in probas.items():
        fpr, tpr, _ = roc_curve(y_true, p)
        ax[0].plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y_true, p):.3f})")
        prec, rec, _ = precision_recall_curve(y_true, p)
        ax[1].plot(rec, prec, label=f"{name} (AP={average_precision_score(y_true, p):.3f})")
    ax[0].plot([0, 1], [0, 1], "k--", lw=0.8)
    ax[0].set(title="ROC curve (test set)", xlabel="False positive rate", ylabel="True positive rate")
    ax[1].axhline(np.mean(y_true), color="k", ls="--", lw=0.8, label="Base rate")
    ax[1].set(title="Precision-Recall curve (test set)", xlabel="Recall", ylabel="Precision")
    for a in ax:
        a.legend(loc="lower right" if a is ax[0] else "upper right")
    _save(fig, "model_roc_pr.png")


def plot_confusion(y_true, proba, threshold):
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ConfusionMatrixDisplay.from_predictions(
        y_true, (proba >= threshold).astype(int), display_labels=["Kept", "Canceled"],
        cmap="Blues", ax=ax, colorbar=False,
    )
    ax.set_title(f"Confusion matrix (threshold={threshold:.2f})")
    _save(fig, "model_confusion_matrix.png")


def plot_threshold_curve(y_val, proba_val, threshold):
    prec, rec, thr = precision_recall_curve(y_val, proba_val)
    f1 = 2 * prec[:-1] * rec[:-1] / np.clip(prec[:-1] + rec[:-1], 1e-12, None)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(thr, prec[:-1], label="Precision")
    ax.plot(thr, rec[:-1], label="Recall")
    ax.plot(thr, f1, label="F1", lw=2)
    ax.axvline(threshold, color="k", ls="--", lw=0.8, label=f"Chosen = {threshold:.2f}")
    ax.set(title="Threshold selection (validation set)", xlabel="Decision threshold", ylabel="Score")
    ax.legend()
    _save(fig, "model_threshold_selection.png")


def plot_calibration(y_true, proba):
    frac_pos, mean_pred = calibration_curve(y_true, proba, n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(4.8, 4.5))
    ax.plot(mean_pred, frac_pos, "o-", label="LightGBM")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="Perfect")
    ax.set(title="Calibration (test set)", xlabel="Mean predicted probability",
           ylabel="Observed cancellation rate")
    ax.legend()
    _save(fig, "model_calibration.png")


def plot_importance(names, scores, errs, top=15):
    order = np.argsort(scores)[::-1][:top][::-1]
    fig, ax = plt.subplots(figsize=(7, 5.2))
    ax.barh(np.array(names)[order], np.array(scores)[order], xerr=np.array(errs)[order], color="#4c72b0")
    ax.set(title="Permutation importance on raw features (test set)", xlabel="Drop in ROC-AUC when shuffled")
    _save(fig, "model_permutation_importance.png")
