-- Q6. Top source countries by volume and how risky each one is.
--     `volume_rank` vs `risk_rank` highlights countries that are big AND risky.
WITH by_country AS (
    SELECT
        country,
        COUNT(*)                           AS bookings,
        SUM(is_canceled)                   AS canceled,
        100.0 * AVG(is_canceled)           AS cancel_rate
    FROM bookings
    WHERE country IS NOT NULL
    GROUP BY country
    HAVING COUNT(*) >= 1000
)
SELECT
    country,
    bookings,
    canceled,
    ROUND(cancel_rate, 1)                                   AS cancel_rate_pct,
    RANK() OVER (ORDER BY bookings DESC)                    AS volume_rank,
    RANK() OVER (ORDER BY cancel_rate DESC)                 AS risk_rank
FROM by_country
ORDER BY risk_rank;
