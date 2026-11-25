import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def load_and_prepare(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    df["arrival_month_num"] = df["arrival_date_month"].map(MONTH_MAP)
    df["arrival_date"] = pd.to_datetime(
        dict(
            year=df["arrival_date_year"],
            month=df["arrival_month_num"],
            day=df["arrival_date_day_of_month"],
        ),
        errors="coerce",
    )
    df["reservation_status_date"] = pd.to_datetime(
        df["reservation_status_date"], errors="coerce"
    )

    int_cols = [
        "is_canceled", "lead_time", "arrival_date_year",
        "arrival_date_day_of_month", "arrival_month_num",
        "stays_in_weekend_nights", "stays_in_week_nights",
        "adults", "children", "babies",
        "is_repeated_guest", "previous_cancellations",
        "previous_bookings_not_canceled", "booking_changes",
        "days_in_waiting_list", "required_car_parking_spaces",
        "total_of_special_requests",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    float_cols = ["adr", "agent", "company"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Load hotel_bookings.csv into SQLite or PostgreSQL")
    parser.add_argument("--csv", type=Path, default=Path("data/hotel_bookings.csv"))
    parser.add_argument("--db-url", type=str, default=os.getenv("DATABASE_URL", "sqlite:///data/hotel_bookings.db"))
    parser.add_argument("--table", type=str, default="hotel_bookings")
    args = parser.parse_args()

    df = load_and_prepare(args.csv)
    engine = create_engine(args.db_url)

    df.to_sql(args.table, engine, if_exists="replace", index=False, chunksize=5000)

    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {args.table}")).scalar()
        print(f"Loaded {count} rows into '{args.table}' ({args.db_url}).")


if __name__ == "__main__":
    main()