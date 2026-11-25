-- Q7. One-table risk profile: cancellation rate for each value of the
--     business levers most associated with cancelling. `lift` compares each
--     group with the overall rate (>1 = riskier than average).
WITH base AS (
    SELECT
        is_canceled,
        deposit_type,
        customer_type,
        CASE WHEN previous_cancellations > 0 THEN 'has prior cancellation'
             ELSE 'no prior cancellation' END                          AS history,
        CASE WHEN total_of_special_requests > 0 THEN 'has special request'
             ELSE 'no special request' END                             AS requests,
        CASE WHEN required_car_parking_spaces > 0 THEN 'needs parking'
             ELSE 'no parking' END                                     AS parking,
        CASE WHEN is_repeated_guest = 1 THEN 'repeat guest'
             ELSE 'first-time guest' END                               AS guest_type,
        CASE WHEN booking_changes > 0 THEN 'changed booking'
             ELSE 'never changed' END                                  AS changes
    FROM bookings
),
long_form AS (
    SELECT 'deposit_type' AS dimension, deposit_type AS value, is_canceled FROM base UNION ALL
    SELECT 'customer_type', customer_type, is_canceled FROM base UNION ALL
    SELECT 'history',       history,       is_canceled FROM base UNION ALL
    SELECT 'requests',      requests,      is_canceled FROM base UNION ALL
    SELECT 'parking',       parking,       is_canceled FROM base UNION ALL
    SELECT 'guest_type',    guest_type,    is_canceled FROM base UNION ALL
    SELECT 'changes',       changes,       is_canceled FROM base
),
overall AS (SELECT AVG(is_canceled) AS rate FROM base)
SELECT
    dimension,
    value,
    COUNT(*)                                             AS bookings,
    ROUND(100.0 * AVG(is_canceled), 1)                   AS cancel_rate_pct,
    ROUND(AVG(is_canceled) / (SELECT rate FROM overall), 2) AS lift
FROM long_form
GROUP BY dimension, value
ORDER BY dimension, cancel_rate_pct DESC;
