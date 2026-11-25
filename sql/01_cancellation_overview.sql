-- Q1. How big is the cancellation problem for each hotel?
SELECT
    hotel,
    COUNT(*)                                            AS bookings,
    SUM(is_canceled)                                    AS canceled,
    ROUND(100.0 * AVG(is_canceled), 1)                  AS cancel_rate_pct,
    ROUND(AVG(lead_time), 1)                            AS avg_lead_time_days,
    ROUND(AVG(CASE WHEN is_canceled = 0 THEN adr::numeric END), 2) AS avg_adr_realised,
    ROUND(AVG(total_nights), 2)                         AS avg_nights
FROM bookings
GROUP BY hotel
UNION ALL
SELECT
    'ALL HOTELS', COUNT(*), SUM(is_canceled),
    ROUND(100.0 * AVG(is_canceled), 1), ROUND(AVG(lead_time), 1),
    ROUND(AVG(CASE WHEN is_canceled = 0 THEN adr::numeric END), 2), ROUND(AVG(total_nights), 2)
FROM bookings;
