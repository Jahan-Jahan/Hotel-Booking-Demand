"""Load the CSV into PostgreSQL and run every analysis query in sql/.

Usage:  python -m src.run_sql
Results are printed and saved as CSV in reports/sql_results/.
"""
from src.config import SQL_DIR, SQL_RESULTS_DIR
from src.db import get_engine, load_csv, run_query, run_script


def main():
    SQL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    print(f"Loaded {load_csv(engine):,} raw rows into PostgreSQL")
    run_script(engine, SQL_DIR / "00_setup.sql")

    for path in sorted(SQL_DIR.glob("0[1-9]_*.sql")):
        result = run_query(engine, path.read_text())
        out = SQL_RESULTS_DIR / f"{path.stem}.csv"
        result.to_csv(out, index=False)
        print(f"\n=== {path.name} ({len(result)} rows) -> {out.name}")
        print(result.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
