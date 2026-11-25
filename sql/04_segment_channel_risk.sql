-- Q4. Which market-segment x distribution-channel combinations are riskiest?
--     Ranked with RANK(); small groups removed with HAVING.
SELECT
    market_segment,
    distribution_channel,
    COUNT(*)                                              AS bookings,
    ROUND(100.0 * AVG(is_canceled), 1)                    AS cancel_rate_pct,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)    AS share_of_bookings_pct,
    RANK() OVER (ORDER BY AVG(is_canceled) DESC)          AS risk_rank
FROM bookings
GROUP BY market_segment, distribution_channel
HAVING COUNT(*) >= 500
ORDER BY risk_rank;
