from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
import joblib
import pandas as pd
from pydantic import BaseModel, Field


MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/model.joblib"))
DEFAULT_THRESHOLD = float(os.getenv("DECISION_THRESHOLD", "0.5"))


class BookingFeatures(BaseModel):
    hotel: str = Field(..., examples=["City Hotel"])
    lead_time: int = Field(..., ge=0, examples=[45])
    arrival_date_year: int = Field(..., examples=[2017])
    arrival_date_month: str = Field(..., examples=["July"])
    arrival_date_day_of_month: int = Field(..., ge=1, le=31, examples=[15])
    stays_in_weekend_nights: int = Field(..., ge=0, examples=[1])
    stays_in_week_nights: int = Field(..., ge=0, examples=[2])
    adults: int = Field(..., ge=0, examples=[2])
    children: float = Field(0.0, ge=0, examples=[0.0])
    babies: int = Field(0, ge=0, examples=[0])
    meal: str = Field("BB", examples=["BB"])
    country: str = Field("PRT", examples=["PRT"])
    market_segment: str = Field("Online TA", examples=["Online TA"])
    distribution_channel: str = Field("TA/TO", examples=["TA/TO"])
    is_repeated_guest: int = Field(0, ge=0, le=1, examples=[0])
    previous_cancellations: int = Field(0, ge=0, examples=[0])
    previous_bookings_not_canceled: int = Field(0, ge=0, examples=[0])
    reserved_room_type: str = Field("A", examples=["A"])
    booking_changes: int = Field(0, ge=0, examples=[0])
    deposit_type: str = Field("No Deposit", examples=["No Deposit"])
    agent: float | None = Field(None, examples=[9.0])
    company: float | None = Field(None, examples=[None])
    customer_type: str = Field("Transient", examples=["Transient"])
    adr: float = Field(..., examples=[110.0])
    required_car_parking_spaces: int = Field(0, ge=0, examples=[0])
    total_of_special_requests: int = Field(0, ge=0, examples=[1])


class PredictionResponse(BaseModel):
    cancel_probability: float
    will_cancel: bool
    threshold_used: float


artifacts: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")
    loaded = joblib.load(MODEL_PATH)
    if isinstance(loaded, dict):
        artifacts["pipeline"] = loaded["pipeline"]
        artifacts["threshold"] = float(loaded.get("threshold", DEFAULT_THRESHOLD))
    else:
        artifacts["pipeline"] = loaded
        artifacts["threshold"] = DEFAULT_THRESHOLD
    yield
    artifacts.clear()


app = FastAPI(title="Hotel Cancellation Prediction API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: BookingFeatures) -> PredictionResponse:
    pipeline = artifacts.get("pipeline")
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    df = pd.DataFrame([payload.model_dump()])
    prob = float(pipeline.predict_proba(df)[:, 1][0])
    threshold = float(artifacts.get("threshold", DEFAULT_THRESHOLD))

    return PredictionResponse(
        cancel_probability=round(prob, 6),
        will_cancel=prob >= threshold,
        threshold_used=threshold,
    )