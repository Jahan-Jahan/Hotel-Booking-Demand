"""Central configuration: paths, constants and the split dates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "hotel_bookings.csv"
DB_PATH = ROOT / "data" / "hotel.db"
MODEL_PATH = ROOT / "models" / "model.joblib"
SQL_DIR = ROOT / "sql"
REPORTS_DIR = ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"
SQL_RESULTS_DIR = REPORTS_DIR / "sql_results"

TARGET = "is_canceled"
RANDOM_STATE = 42

# Time-based split on the *arrival date* (data covers 2015-07 .. 2017-08).
# train: before VAL_START | validation: [VAL_START, TEST_START) | test: >= TEST_START
VAL_START = "2017-03-01"
TEST_START = "2017-06-01"

MONTH_TO_NUM = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}
