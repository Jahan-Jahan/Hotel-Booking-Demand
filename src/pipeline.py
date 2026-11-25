"""Model pipelines (preprocessing + estimator)."""
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.config import RANDOM_STATE
from src.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, add_features


def build_preprocessor() -> Pipeline:
    """Raw booking frame -> numeric matrix (feature engineering + encoding)."""
    encode = ColumnTransformer(
        [
            ("num", Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(
                handle_unknown="infrequent_if_exist", min_frequency=50,
                sparse_output=True,
            ), CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline([
        ("features", FunctionTransformer(add_features, validate=False)),
        ("encode", encode),
    ])


def lgbm_params() -> dict:
    return dict(
        # Small, strongly regularised trees: chosen on the VALIDATION set among a
        # handful of configs (bigger trees overfit the 2015-16 period and
        # early-stopped after ~70 rounds because of the cancellation-rate drift).
        n_estimators=3000, learning_rate=0.03, num_leaves=7,
        min_child_samples=100, subsample=0.8, subsample_freq=1,
        colsample_bytree=0.5, reg_lambda=5.0, random_state=RANDOM_STATE,
        n_jobs=-1, verbose=-1,
    )


def build_lgbm_pipeline(**overrides) -> Pipeline:
    params = {**lgbm_params(), **overrides}
    return Pipeline([("prep", build_preprocessor()), ("model", LGBMClassifier(**params))])


def build_logreg_pipeline() -> Pipeline:
    return Pipeline([
        ("prep", build_preprocessor()),
        ("model", LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs")),
    ])
