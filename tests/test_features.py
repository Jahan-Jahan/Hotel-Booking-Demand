import pandas as pd

from src.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, add_features

LEAKY = {"reservation_status", "reservation_status_date", "assigned_room_type", "is_canceled"}


def _row(**overrides):
    row = dict(
        hotel="City Hotel", lead_time=45, arrival_date_year=2017, arrival_date_month="July",
        arrival_date_day_of_month=15, stays_in_weekend_nights=1, stays_in_week_nights=2,
        adults=2, children=0.0, babies=0, meal="BB", country="PRT",
        market_segment="Online TA", distribution_channel="TA/TO", is_repeated_guest=0,
        previous_cancellations=0, previous_bookings_not_canceled=0, reserved_room_type="A",
        booking_changes=0, deposit_type="No Deposit", agent=None, company=None,
        customer_type="Transient", adr=110.0, required_car_parking_spaces=0,
        total_of_special_requests=1,
    )
    row.update(overrides)
    return pd.DataFrame([row])


def test_output_columns_and_no_leakage():
    out = add_features(_row())
    assert list(out.columns) == NUMERIC_FEATURES + CATEGORICAL_FEATURES
    assert not LEAKY & set(out.columns)


def test_derived_values():
    out = add_features(_row()).iloc[0]
    assert out["total_nights"] == 3
    assert out["total_guests"] == 2
    assert out["total_price"] == 330.0
    assert out["arrival_month"] == 7
    assert out["arrival_dow"] == 5          # 2017-07-15 was a Saturday
    assert out["has_agent"] == 0 and out["agent_id"] == "-1"


def test_handles_missing_and_agent_id():
    out = add_features(_row(agent=9.0, children=None, company=45.0)).iloc[0]
    assert out["agent_id"] == "9" and out["has_agent"] == 1 and out["has_company"] == 1
    assert out["total_guests"] == 2        # missing children counted as 0


def test_prev_cancel_ratio():
    out = add_features(_row(previous_cancellations=3, previous_bookings_not_canceled=1)).iloc[0]
    assert out["prev_cancel_ratio"] == 0.75


def test_invalid_date_does_not_crash():
    out = add_features(_row(arrival_date_month="February", arrival_date_day_of_month=31))
    assert out["arrival_month"].isna().all()
