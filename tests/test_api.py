"""API tests. A small model is trained on a sample so tests are fast and do not
depend on models/model.joblib being present."""
import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.config import DATA_PATH, TARGET
from src.features import RAW_FEATURES
from src.pipeline import build_lgbm_pipeline

VALID = dict(
    hotel="City Hotel", lead_time=45, arrival_date_year=2017, arrival_date_month="July",
    arrival_date_day_of_month=15, stays_in_weekend_nights=1, stays_in_week_nights=2,
    adults=2, adr=110.0,
)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    df = pd.read_csv(DATA_PATH).drop_duplicates().sample(4000, random_state=0)
    pipe = build_lgbm_pipeline(n_estimators=30, n_jobs=1).fit(df[RAW_FEATURES], df[TARGET])
    path = tmp_path_factory.mktemp("model") / "model.joblib"
    joblib.dump({"pipeline": pipe, "threshold": 0.3}, path)
    app_module.MODEL_PATH = path
    with TestClient(app_module.app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_predict_minimal_payload(client):
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["cancel_probability"] <= 1.0
    assert body["threshold_used"] == 0.3
    assert body["will_cancel"] == (body["cancel_probability"] >= 0.3)


def test_predict_full_payload_with_agent(client):
    r = client.post("/predict", json={**VALID, "agent": 9.0, "company": None, "country": "GBR",
                                      "deposit_type": "Non Refund", "children": 1.0})
    assert r.status_code == 200


def test_longer_lead_time_not_less_risky_than_same_day(client):
    far = client.post("/predict", json={**VALID, "lead_time": 300}).json()["cancel_probability"]
    near = client.post("/predict", json={**VALID, "lead_time": 0}).json()["cancel_probability"]
    assert far > near


def test_validation_errors(client):
    assert client.post("/predict", json={**VALID, "lead_time": -1}).status_code == 422
    bad = {k: v for k, v in VALID.items() if k != "adr"}
    assert client.post("/predict", json=bad).status_code == 422
