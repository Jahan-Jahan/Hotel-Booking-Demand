-- Analysis layer on top of the raw table `hotel_bookings` (loaded by src/db.py).
-- Same cleaning rules as the Python pipeline (src/train.py:load_clean_data):
-- exact duplicate rows removed, then zero-guest bookings and negative ADR dropped.
-- Adds month number, year-month, nights and potential revenue (ADR x nights).
-- It is a MATERIALIZED view (computed once, indexed) because DISTINCT over
-- 119k rows is too expensive to repeat for every query.
DROP MATERIALIZED VIEW IF EXISTS bookings;

CREATE MATERIALIZED VIEW bookings AS
WITH dedup AS (
    SELECT DISTINCT * FROM hotel_bookings
),
typed AS (
    SELECT
        d.*,
        CASE arrival_date_month
            WHEN 'January' THEN 1  WHEN 'February' THEN 2  WHEN 'March' THEN 3
            WHEN 'April' THEN 4    WHEN 'May' THEN 5       WHEN 'June' THEN 6
            WHEN 'July' THEN 7     WHEN 'August' THEN 8    WHEN 'September' THEN 9
            WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
        END AS month_num
    FROM dedup AS d
)
SELECT
    t.*,
    TO_CHAR(MAKE_DATE(arrival_date_year::int, month_num, arrival_date_day_of_month::int), 'YYYY-MM') AS year_month,
    stays_in_weekend_nights + stays_in_week_nights                                         AS total_nights,
    (adr::numeric * (stays_in_weekend_nights + stays_in_week_nights))                      AS potential_revenue
FROM typed AS t
WHERE adults + COALESCE(children, 0) + babies > 0
  AND adr >= 0;

CREATE INDEX idx_bookings_year_month ON bookings (year_month);
CREATE INDEX idx_bookings_hotel      ON bookings (hotel);
CREATE INDEX idx_bookings_country    ON bookings (country);
ANALYZE bookings;
