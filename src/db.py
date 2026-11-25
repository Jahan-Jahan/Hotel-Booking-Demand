import os
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text


DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/hotel_db"


def get_engine(db_url: Optional[str] = None):
    url = db_url or os.getenv("DATABASE_URL") or DEFAULT_DB_URL
    return create_engine(url)


def read_bookings_from_db(table: str = "hotel_bookings", db_url: Optional[str] = None) -> pd.DataFrame:
    engine = get_engine(db_url)
    query = text(f"SELECT * FROM {table}")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df