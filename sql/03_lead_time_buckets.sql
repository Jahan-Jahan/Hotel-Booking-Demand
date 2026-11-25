-- Q3. Cancellation rate by lead-time bucket, split by hotel.
WITH bucketed AS (
    SELECT
        hotel, is_canceled,
        CASE
            WHEN lead_time <= 7   THEN '1) 0-7 days'
            WHEN lead_time <= 30  THEN '2) 8-30 days'
            WHEN lead_time <= 90  THEN '3) 31-90 days'
            WHEN lead_time <= 180 THEN '4) 91-180 days'
            WHEN lead_time <= 365 THEN '5) 181-365 days'
            ELSE                       '6) >365 days'
        END AS lead_bucket
    FROM bookings
)
SELECT
    lead_bucket,
    hotel,
    COUNT(*)                           AS bookings,
    ROUND(100.0 * AVG(is_canceled), 1) AS cancel_rate_pct
FROM bucketed
GROUP BY lead_bucket, hotel
ORDER BY lead_bucket, hotel;
