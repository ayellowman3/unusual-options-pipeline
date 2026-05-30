-- Top 25 unusual contracts by score and volume.
SELECT
    contract_symbol,
    symbol,
    option_type,
    strike,
    expiration_date,
    volume,
    open_interest,
    volume_open_interest_ratio,
    implied_volatility,
    unusual_activity_score
FROM fact_options_event
WHERE unusual_activity_score > 0
ORDER BY unusual_activity_score DESC, volume DESC, COALESCE(volume_open_interest_ratio, 0) DESC
LIMIT 25;

-- Unusual activity count by symbol.
SELECT
    symbol,
    COUNT(*) AS unusual_event_count
FROM fact_options_event
WHERE unusual_activity_score > 0
GROUP BY symbol
ORDER BY unusual_event_count DESC, symbol ASC;

-- Flag distribution.
SELECT
    flag,
    COUNT(*) AS flag_count
FROM fact_unusual_activity
GROUP BY flag
ORDER BY flag_count DESC, flag ASC;

-- Call vs put unusual activity.
SELECT
    option_type,
    COUNT(*) AS unusual_event_count,
    SUM(volume) AS total_volume
FROM fact_options_event
WHERE unusual_activity_score > 0
GROUP BY option_type
ORDER BY option_type ASC;

-- Highest volume/open interest ratio contracts.
SELECT
    contract_symbol,
    symbol,
    volume,
    open_interest,
    volume_open_interest_ratio,
    unusual_activity_score
FROM fact_options_event
WHERE volume_open_interest_ratio IS NOT NULL
ORDER BY volume_open_interest_ratio DESC, volume DESC
LIMIT 25;

-- Average IV by symbol.
SELECT
    symbol,
    ROUND(AVG(implied_volatility), 4) AS avg_implied_volatility
FROM fact_options_event
GROUP BY symbol
ORDER BY avg_implied_volatility DESC, symbol ASC;

-- Intraday unusual activity count by hour.
SELECT
    DATE_TRUNC('hour', event_timestamp) AS event_hour,
    COUNT(*) AS unusual_event_count
FROM fact_options_event
WHERE unusual_activity_score > 0
GROUP BY event_hour
ORDER BY event_hour ASC;

-- Top symbols by total volume.
SELECT
    symbol,
    SUM(volume) AS total_volume
FROM fact_options_event
GROUP BY symbol
ORDER BY total_volume DESC, symbol ASC
LIMIT 25;
