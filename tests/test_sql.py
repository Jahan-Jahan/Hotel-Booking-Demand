"""Integration test for the PostgreSQL analysis layer (skipped if no database)."""
import pytest
from sqlalchemy import text

from src.config import SQL_DIR
from src.db import get_engine, load_csv, run_query, run_script


@pytest.fixture(scope="module")
def engine():
    eng = get_engine()
    try:
        with eng.connect() as con:
            con.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("PostgreSQL not reachable (run `make db-up`)")
    load_csv(eng)
    run_script(eng, SQL_DIR / "00_setup.sql")
    return eng


def test_view_matches_python_cleaning(engine):
    n, rate = run_query(engine, "SELECT COUNT(*) AS n, AVG(is_canceled) AS r FROM bookings").iloc[0]
    assert n == 87_229
    assert round(float(rate), 3) == 0.275


@pytest.mark.parametrize("path", sorted(SQL_DIR.glob("0[1-9]_*.sql")), ids=lambda p: p.name)
def test_every_query_runs(engine, path):
    assert len(run_query(engine, path.read_text())) > 0
