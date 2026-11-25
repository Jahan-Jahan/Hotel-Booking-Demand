"""PostgreSQL helpers: connection, CSV loading and query execution."""
import io
import os

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import DATA_PATH, DEFAULT_DATABASE_URL

RAW_TABLE = "hotel_bookings"


def get_engine() -> Engine:
    """Engine from $DATABASE_URL (falls back to the docker-compose default)."""
    return create_engine(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL), future=True)


def load_csv(engine: Engine, csv_path=DATA_PATH, table: str = RAW_TABLE) -> int:
    """(Re)create `table` from the CSV and bulk-load it with COPY (fast)."""
    df = pd.read_csv(csv_path)
    with engine.begin() as con:
        con.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS bookings"))
        df.head(0).to_sql(table, con, if_exists="replace", index=False)  # column types only
        buf = io.StringIO()
        df.to_csv(buf, index=False, header=False)
        buf.seek(0)
        cols = ", ".join(f'"{c}"' for c in df.columns)
        with con.connection.cursor() as cur, cur.copy(
            f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv)"
        ) as copy:
            while chunk := buf.read(1 << 20):
                copy.write(chunk)
    return len(df)


def run_script(engine: Engine, path) -> None:
    """Execute a multi-statement SQL file (DDL such as 00_setup.sql)."""
    with engine.begin() as con:
        con.exec_driver_sql(path.read_text())


def run_query(engine: Engine, sql: str) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame."""
    with engine.connect() as con:
        return pd.read_sql_query(text(sql), con)
