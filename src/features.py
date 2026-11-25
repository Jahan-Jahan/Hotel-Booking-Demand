"""Feature engineering.

Everything here lives *inside* the sklearn pipeline (via FunctionTransformer),
so the API only needs the raw booking fields and can never drift away from
the training-time logic.
"""
import numpy as np
import pandas as pd

from src.config import MONTH_TO_NUM

# The raw columns the model (and the API) accepts. Deliberately EXCLUDED because
# they leak the outcome or are only known after it:
#   reservation_status, reservation_status_date, assigned_room_type,
#   days_in_waiting_list, arrival_date_week_number (re-derived from the date)
RAW_FEATURES = [
    "hotel", "lead_time", "arrival_date_year", "arrival_date_month",
    "arrival_date_day_of_month", "stays_in_weekend_nights",
    "stays_in_week_nights", "adults", "children", "babies", "meal", "country",
    "market_segment", "distribution_channel", "is_repeated_guest",
    "previous_cancellations", "previous_bookings_not_canceled",
    "reserved_room_type", "booking_changes", "deposit_type", "agent",
    "company", "customer_type", "adr", "required_car_parking_spaces",
    "total_of_special_requests",
]

# Features that are typically set/updated AFTER the booking is made. Used only
# for the "booking-time only" ablation in train.py.
POST_BOOKING_FEATURES = [
    "booking_changes", "required_car_parking_spaces", "total_of_special_requests",
]

_RAW_NUMERIC = [
    "lead_time", "stays_in_weekend_nights", "stays_in_week_nights", "adults",
    "children", "babies", "is_repeated_guest", "previous_cancellations",
    "previous_bookings_not_canceled", "booking_changes", "adr",
    "required_car_parking_spaces", "total_of_special_requests",
]

CATEGORICAL_FEATURES = [
    "hotel", "meal", "country", "market_segment", "distribution_channel",
    "reserved_room_type", "deposit_type", "customer_type", "agent_id",
]

NUMERIC_FEATURES = _RAW_NUMERIC + [
    "arrival_month", "arrival_week", "arrival_dow", "arrival_day",
    "total_nights", "total_guests", "has_children", "weekend_share",
    "adr_per_person", "total_price", "has_agent", "has_company",
    "prev_cancel_ratio",
]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn raw booking rows into the model's input frame.

    Robust to the types the API produces (None for agent/company, etc.).
    """
    df = df.copy()

    for col in _RAW_NUMERIC + ["agent", "company"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Arrival-date features (year is intentionally NOT used: with a time-based
    # split it would just encode "which period", which cannot generalise).
    arrival = pd.to_datetime(
        {
            "year": df["arrival_date_year"],
            "month": df["arrival_date_month"].map(MONTH_TO_NUM),
            "day": df["arrival_date_day_of_month"],
        },
        errors="coerce",
    )
    df["arrival_month"] = arrival.dt.month
    df["arrival_week"] = arrival.dt.isocalendar().week.astype("float")
    df["arrival_dow"] = arrival.dt.dayofweek
    df["arrival_day"] = arrival.dt.day

    # Stay / party features
    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["total_guests"] = df["adults"] + df["children"].fillna(0) + df["babies"]
    df["has_children"] = ((df["children"].fillna(0) + df["babies"]) > 0).astype(int)
    df["weekend_share"] = np.where(
        df["total_nights"] > 0, df["stays_in_weekend_nights"] / df["total_nights"], 0.0
    )
    df["adr_per_person"] = np.where(df["total_guests"] > 0, df["adr"] / df["total_guests"], np.nan)
    df["total_price"] = df["adr"] * df["total_nights"]

    # Customer history
    prior = df["previous_cancellations"] + df["previous_bookings_not_canceled"]
    df["prev_cancel_ratio"] = np.where(prior > 0, df["previous_cancellations"] / prior, 0.0)

    # Agent / company: ids are anonymised, so use the agent id as a category
    # and only a presence flag for company (112k/119k are missing).
    df["has_agent"] = df["agent"].notna().astype(int)
    df["has_company"] = df["company"].notna().astype(int)
    df["agent_id"] = df["agent"].fillna(-1).astype(int).astype(str)

    for col in ["hotel", "meal", "country", "market_segment", "distribution_channel",
                "reserved_room_type", "deposit_type", "customer_type"]:
        df[col] = df[col].astype("object").where(df[col].notna(), "missing").astype(str)

    return df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
