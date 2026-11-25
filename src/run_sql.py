"""Load the CSV into SQLite and run every query in sql/.

Usage:  python -m src.run_sql
Results are printed and saved as CSV in reports/sql_results/.
"""
import sqlite3

import pandas as pd

from src.config import DATA_PATH, DB_PATH, SQL_DIR, SQL_RESULTS_DIR


def main():
    SQL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.read_csv(DATA_PATH).to_sql(
        "hotel_bookings", sqlite3.connect(DB_PATH), if_exists="replace", index=False
    )
    with sqlite3.connect(DB_PATH) as con:
        con.executescript((SQL_DIR / "00_setup.sql").read_text())
        for path in sorted(SQL_DIR.glob("0[1-9]_*.sql")):
            result = pd.read_sql_query(path.read_text(), con)
            out = SQL_RESULTS_DIR / f"{path.stem}.csv"
            result.to_csv(out, index=False)
            print(f"\n=== {path.name} ({len(result)} rows) -> {out.name}")
            print(result.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
