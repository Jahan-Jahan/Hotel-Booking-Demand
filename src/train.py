"""Train, evaluate and save the cancellation model.

Usage (from the repository root):
    python -m src.train

Design choices
--------------
* Leakage-free: only booking-time fields listed in `features.RAW_FEATURES`.
* Exact duplicate rows are dropped (~27% of the raw file).
* Time-based split on arrival date: train < 2017-03 <= val < 2017-06 <= test.
  Early stopping and the decision threshold use the validation set only; the
  test set is touched once, for the final report.
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
import lightgbm as lgb

from src import evaluate as ev
from src.config import (
    DATA_PATH, MODEL_PATH, MONTH_TO_NUM, RANDOM_STATE, REPORTS_DIR, TARGET,
    TEST_START, VAL_START,
)
from src.features import POST_BOOKING_FEATURES, RAW_FEATURES
from src.pipeline import build_logreg_pipeline, build_preprocessor, lgbm_params


def load_clean_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    n_raw = len(df)
    df = df.drop_duplicates()
    guests = df["adults"] + df["children"].fillna(0) + df["babies"]
    df = df[(guests > 0) & (df["adr"] >= 0)].copy()
    df["arrival_date"] = pd.to_datetime(
        dict(year=df["arrival_date_year"],
             month=df["arrival_date_month"].map(MONTH_TO_NUM),
             day=df["arrival_date_day_of_month"])
    )
    print(f"Rows: raw={n_raw:,} -> clean={len(df):,}")
    return df.sort_values("arrival_date").reset_index(drop=True)


def time_split(df):
    d = df["arrival_date"]
    return (df[d < VAL_START], df[(d >= VAL_START) & (d < TEST_START)], df[d >= TEST_START])


def fit_lgbm(train, val, features):
    """Fit preprocessing, then LightGBM with early stopping on the validation set."""
    prep = build_preprocessor()
    X_tr = prep.fit_transform(train[features])
    X_va = prep.transform(val[features])
    model = lgb.LGBMClassifier(**lgbm_params())
    model.fit(
        X_tr, train[TARGET], eval_X=X_va, eval_y=val[TARGET], eval_metric="auc",
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )
    return Pipeline([("prep", prep), ("model", model)])


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    df = load_clean_data()
    train, val, test = time_split(df)
    for name, part in [("train", train), ("val", val), ("test", test)]:
        print(f"{name:5s}: {len(part):>6,} rows | cancel rate {part[TARGET].mean():.3f} "
              f"| {part['arrival_date'].min().date()} -> {part['arrival_date'].max().date()}")
    y_val, y_test = val[TARGET].to_numpy(), test[TARGET].to_numpy()

    # ---- Baselines -------------------------------------------------------
    results = {}
    dummy = DummyClassifier(strategy="prior").fit(train[RAW_FEATURES], train[TARGET])
    p = dummy.predict_proba(test[RAW_FEATURES])[:, 1]
    results["majority_baseline"] = {"roc_auc": 0.5, "pr_auc": round(float(y_test.mean()), 4)}

    logreg = build_logreg_pipeline().fit(train[RAW_FEATURES], train[TARGET])
    p_lr_val = logreg.predict_proba(val[RAW_FEATURES])[:, 1]
    thr_lr = ev.best_f1_threshold(y_val, p_lr_val)
    p_lr = logreg.predict_proba(test[RAW_FEATURES])[:, 1]
    results["logistic_regression"] = ev.compute_metrics(y_test, p_lr, thr_lr)

    # ---- LightGBM (main model) -------------------------------------------
    pipe = fit_lgbm(train, val, RAW_FEATURES)
    best_iter = int(pipe.named_steps["model"].best_iteration_)
    p_val = pipe.predict_proba(val[RAW_FEATURES])[:, 1]
    threshold = ev.best_f1_threshold(y_val, p_val)
    p_test = pipe.predict_proba(test[RAW_FEATURES])[:, 1]
    results["lightgbm"] = ev.compute_metrics(y_test, p_test, threshold)
    results["lightgbm"]["best_iteration"] = best_iter

    # ---- Ablation: only features known when the booking is made -----------
    # Post-booking columns are neutralised (constant 0) so they carry no signal.
    def neutralise(part):
        part = part.copy()
        part[POST_BOOKING_FEATURES] = 0
        return part

    tr_bt, va_bt, te_bt = neutralise(train), neutralise(val), neutralise(test)
    pipe_bt = fit_lgbm(tr_bt, va_bt, RAW_FEATURES)
    thr_bt = ev.best_f1_threshold(y_val, pipe_bt.predict_proba(va_bt[RAW_FEATURES])[:, 1])
    results["lightgbm_booking_time_only"] = ev.compute_metrics(
        y_test, pipe_bt.predict_proba(te_bt[RAW_FEATURES])[:, 1], thr_bt)

    print("\nTest-set results")
    print(pd.DataFrame(results).T.to_string())

    # ---- Plots -------------------------------------------------------------
    ev.plot_roc_pr(y_test, {"Logistic regression": p_lr, "LightGBM": p_test})
    ev.plot_confusion(y_test, p_test, threshold)
    ev.plot_threshold_curve(y_val, p_val, threshold)
    ev.plot_calibration(y_test, p_test)

    # Permutation importance on RAW columns (engineered features are inside the
    # pipeline, so this is directly interpretable for the business).
    rng = np.random.RandomState(RANDOM_STATE)
    idx = rng.choice(len(test), size=min(8000, len(test)), replace=False)
    imp = permutation_importance(
        pipe, test.iloc[idx][RAW_FEATURES], y_test[idx], scoring="roc_auc",
        n_repeats=3, random_state=RANDOM_STATE, n_jobs=1,
    )
    ev.plot_importance(RAW_FEATURES, imp.importances_mean, imp.importances_std)
    results["top_features"] = [RAW_FEATURES[i] for i in np.argsort(imp.importances_mean)[::-1][:10]]

    # ---- Save artifacts ------------------------------------------------------
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(
        {"pipeline": pipe, "threshold": threshold,
         "metadata": {"features": RAW_FEATURES, "test_metrics": results["lightgbm"],
                      "split": {"val_start": VAL_START, "test_start": TEST_START}}},
        MODEL_PATH, compress=3,
    )
    (REPORTS_DIR / "metrics.json").write_text(json.dumps(results, indent=2))
    print(f"\nSaved model -> {MODEL_PATH}\nSaved metrics -> {REPORTS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
