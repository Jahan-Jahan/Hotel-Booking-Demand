-- Q2. Monthly cancellation trend with month-over-month change and a
--     3-month moving average (window functions: LAG, AVG OVER).
WITH monthly AS (
    SELECT
        year_month,
        COUNT(*)                          AS bookings,
        SUM(is_canceled)                  AS canceled,
        100.0 * AVG(is_canceled)          AS cancel_rate
    FROM bookings
    GROUP BY year_month
)
SELECT
    year_month,
    bookings,
    canceled,
    ROUND(cancel_rate, 1)                                                     AS cancel_rate_pct,
    ROUND(cancel_rate - LAG(cancel_rate) OVER (ORDER BY year_month), 1)       AS mom_change_pp,
    ROUND(AVG(cancel_rate) OVER (ORDER BY year_month
                                 ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3m_pct
FROM monthly
ORDER BY year_month;
