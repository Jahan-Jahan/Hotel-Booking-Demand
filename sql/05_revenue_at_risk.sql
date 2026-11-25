-- Q5. Revenue lost to cancellations (ADR x nights of canceled bookings),
--     per hotel and year, as a share of everything that was booked.
WITH rev AS (
    SELECT
        hotel,
        arrival_date_year                                                   AS year,
        SUM(potential_revenue)                                              AS booked_revenue,
        SUM(CASE WHEN is_canceled = 1 THEN potential_revenue ELSE 0 END)    AS lost_revenue
    FROM bookings
    GROUP BY hotel, arrival_date_year
)
SELECT
    hotel,
    year,
    ROUND(booked_revenue)                                   AS booked_revenue_eur,
    ROUND(lost_revenue)                                     AS lost_to_cancellation_eur,
    ROUND(100.0 * lost_revenue / booked_revenue, 1)         AS lost_share_pct,
    ROUND(100.0 * lost_revenue / SUM(lost_revenue) OVER (PARTITION BY year), 1)
                                                            AS share_of_year_losses_pct
FROM rev
ORDER BY year, hotel;
