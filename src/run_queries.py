import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db import get_engine


DEFAULT_OUT_DIR = Path("reports/sql_outputs")


def build_queries(table: str) -> dict[str, tuple[str, str]]:
    return {
        "q1_cancel_by_month": (
            f"""
            SELECT
                arrival_month_num,
                arrival_date_month,
                COUNT(*) AS total_bookings,
                SUM(is_canceled) AS canceled_bookings,
                ROUND(AVG(is_canceled::numeric) * 100.0, 2) AS cancellation_rate_pct
            FROM {table}
            GROUP BY arrival_month_num, arrival_date_month
            ORDER BY arrival_month_num;
            """,
            "Cancellation rates peak during spring and early summer (highest in June at 41.46% and April at 40.80%) compared to winter months (lowest in January at 30.48%).",
        ),
        "q2_cancel_by_lead_time": (
            f"""
            SELECT
                CASE
                    WHEN lead_time BETWEEN 0 AND 7 THEN '00-07 days'
                    WHEN lead_time BETWEEN 8 AND 30 THEN '08-30 days'
                    WHEN lead_time BETWEEN 31 AND 90 THEN '31-90 days'
                    WHEN lead_time BETWEEN 91 AND 180 THEN '91-180 days'
                    ELSE '181+ days'
                END AS lead_time_bucket,
                CASE
                    WHEN lead_time BETWEEN 0 AND 7 THEN 1
                    WHEN lead_time BETWEEN 8 AND 30 THEN 2
                    WHEN lead_time BETWEEN 31 AND 90 THEN 3
                    WHEN lead_time BETWEEN 91 AND 180 THEN 4
                    ELSE 5
                END AS bucket_order,
                COUNT(*) AS total_bookings,
                SUM(is_canceled) AS canceled_bookings,
                ROUND(AVG(is_canceled::numeric) * 100.0, 2) AS cancellation_rate_pct
            FROM {table}
            GROUP BY lead_time_bucket, bucket_order
            ORDER BY bucket_order;
            """,
            "Cancellation rate increases monotonically with lead time, rising from 9.63% for bookings made 0-7 days in advance to 57.01% for bookings made 181+ days ahead.",
        ),
        "q3_adr_by_market_segment": (
            f"""
            SELECT
                market_segment,
                COUNT(*) AS total_bookings,
                COUNT(*) FILTER (WHERE adr > 0) AS positive_adr_bookings,
                ROUND(AVG(adr) FILTER (WHERE adr > 0)::numeric, 2) AS avg_adr_positive_only,
                ROUND(AVG(adr)::numeric, 2) AS avg_adr_all_rows
            FROM {table}
            GROUP BY market_segment
            ORDER BY avg_adr_positive_only DESC NULLS LAST;
            """,
            "Online TA (117.96) and Direct (117.69) generate the highest average positive ADR, whereas Corporate (70.45) and Complementary (34.04) sit at the lower end.",
        ),
        "q4_cumulative_bookings": (
            f"""
            WITH daily_bookings AS (
                SELECT
                    arrival_date::date AS arrival_day,
                    COUNT(*) AS bookings_count
                FROM {table}
                WHERE arrival_date IS NOT NULL
                GROUP BY arrival_date::date
            )
            SELECT
                arrival_day,
                bookings_count,
                SUM(bookings_count) OVER (
                    ORDER BY arrival_day
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cumulative_bookings
            FROM daily_bookings
            ORDER BY arrival_day;
            """,
            "Cumulative arrival bookings grow steadily over time using a running window sum, tracking total booking volume accumulated up to each arrival date.",
        ),
        "q5_mom_cancel_rate_lag": (
            f"""
            WITH monthly_stats AS (
                SELECT
                    arrival_date_year,
                    arrival_month_num,
                    COUNT(*) AS total_bookings,
                    AVG(is_canceled::numeric) * 100.0 AS cancel_rate_pct
                FROM {table}
                GROUP BY arrival_date_year, arrival_month_num
            )
            SELECT
                arrival_date_year,
                arrival_month_num,
                total_bookings,
                ROUND(cancel_rate_pct, 2) AS cancel_rate_pct,
                ROUND(
                    LAG(cancel_rate_pct) OVER (ORDER BY arrival_date_year, arrival_month_num),
                    2
                ) AS prev_month_cancel_rate_pct,
                ROUND(
                    cancel_rate_pct - LAG(cancel_rate_pct) OVER (ORDER BY arrival_date_year, arrival_month_num),
                    2
                ) AS mom_cancel_rate_diff_pp
            FROM monthly_stats
            ORDER BY arrival_date_year, arrival_month_num;
            """,
            "Using LAG reveals sharp month-over-month shifts in cancellation rate, such as a -14.17 percentage point drop in November 2015 followed by a +12.55 percentage point rebound in December 2015.",
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run analytical SQL queries on PostgreSQL")
    parser.add_argument("--db-url", type=str, default=None, help="PostgreSQL connection URL")
    parser.add_argument("--table", type=str, default="hotel_bookings", help="Target table name")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    engine = get_engine(args.db_url)
    queries = build_queries(args.table)

    summary_lines: list[str] = ["# SQL Analytical Results\n"]

    with engine.connect() as conn:
        for name, (sql, insight) in queries.items():
            df = pd.read_sql(text(sql), conn)
            csv_file = args.out_dir / f"{name}.csv"
            df.to_csv(csv_file, index=False)

            print(f"\n=== {name} -> {csv_file} ===")
            print(df.head(12).to_string(index=False))

            summary_lines.append(f"## {name}\n")
            summary_lines.append(f"- **Insight:** {insight}\n")
            summary_lines.append(df.head(12).to_markdown(index=False) + "\n")

    summary_path = args.out_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nSaved summary report to {summary_path}")


if __name__ == "__main__":
    main()