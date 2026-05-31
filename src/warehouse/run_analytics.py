from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TOP_UNUSUAL_CONTRACTS_QUERY = """
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
    unusual_activity_score,
    event_timestamp
FROM fact_options_event
WHERE unusual_activity_score > 0
ORDER BY unusual_activity_score DESC, volume DESC, COALESCE(volume_open_interest_ratio, 0) DESC
LIMIT {limit}
"""

SYMBOL_UNUSUAL_ACTIVITY_QUERY = """
SELECT
    symbol,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE unusual_activity_score > 0) AS unusual_events,
    ROUND(
        COUNT(*) FILTER (WHERE unusual_activity_score > 0)::numeric / NULLIF(COUNT(*), 0),
        4
    ) AS unusual_event_pct,
    SUM(volume) AS total_volume,
    ROUND(AVG(implied_volatility), 4) AS avg_implied_volatility,
    ROUND(AVG(unusual_activity_score), 4) AS avg_unusual_activity_score
FROM fact_options_event
GROUP BY symbol
ORDER BY unusual_events DESC, total_volume DESC
"""

FLAG_DISTRIBUTION_QUERY = """
SELECT
    flag,
    COUNT(*) AS flag_count
FROM fact_unusual_activity
GROUP BY flag
ORDER BY flag_count DESC, flag ASC
"""

CALL_PUT_UNUSUAL_ACTIVITY_QUERY = """
SELECT
    option_type,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE unusual_activity_score > 0) AS unusual_events,
    ROUND(
        COUNT(*) FILTER (WHERE unusual_activity_score > 0)::numeric / NULLIF(COUNT(*), 0),
        4
    ) AS unusual_event_pct,
    SUM(volume) AS total_volume,
    ROUND(AVG(implied_volatility), 4) AS avg_implied_volatility
FROM fact_options_event
GROUP BY option_type
ORDER BY option_type ASC
"""

HIGHEST_VOLUME_OI_RATIO_QUERY = """
SELECT
    contract_symbol,
    symbol,
    option_type,
    volume,
    open_interest,
    volume_open_interest_ratio,
    unusual_activity_score
FROM fact_options_event
WHERE volume_open_interest_ratio IS NOT NULL
ORDER BY volume_open_interest_ratio DESC, volume DESC
LIMIT {limit}
"""

INTRADAY_UNUSUAL_ACTIVITY_QUERY = """
SELECT
    DATE_TRUNC('hour', event_timestamp) AS event_hour,
    COUNT(*) AS unusual_events
FROM fact_options_event
WHERE unusual_activity_score > 0
GROUP BY DATE_TRUNC('hour', event_timestamp)
ORDER BY event_hour ASC
"""

TOP_SYMBOLS_BY_VOLUME_QUERY = """
SELECT
    symbol,
    SUM(volume) AS total_volume,
    COUNT(*) AS total_events,
    ROUND(SUM(volume)::numeric / NULLIF(COUNT(*), 0), 4) AS avg_volume_per_event
FROM fact_options_event
GROUP BY symbol
ORDER BY total_volume DESC, total_events DESC
LIMIT {limit}
"""


def get_connection():
    import psycopg2

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "unusual_options"),
        user=os.getenv("POSTGRES_USER", "unusual_user"),
        password=os.getenv("POSTGRES_PASSWORD", "unusual_password"),
    )


def build_top_unusual_contracts_query(limit: int) -> str:
    return TOP_UNUSUAL_CONTRACTS_QUERY.format(limit=limit)


def build_highest_volume_oi_ratio_query(limit: int) -> str:
    return HIGHEST_VOLUME_OI_RATIO_QUERY.format(limit=limit)


def build_top_symbols_by_volume_query(limit: int) -> str:
    return TOP_SYMBOLS_BY_VOLUME_QUERY.format(limit=limit)


def run_query(query: str) -> tuple[list[str], list[tuple]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

    return columns, rows


def print_results(title: str, columns: list[str], rows: list[tuple]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(" | ".join(columns))

    if not rows:
        print("(no rows)")
        return

    for row in rows:
        print(" | ".join(str(value) for value in row))


def run_analytics(limit: int = 25) -> None:
    queries = [
        ("Top Unusual Contracts", build_top_unusual_contracts_query(limit)),
        ("Unusual Activity Count By Symbol", SYMBOL_UNUSUAL_ACTIVITY_QUERY),
        ("Flag Distribution", FLAG_DISTRIBUTION_QUERY),
        ("Call Vs Put Unusual Activity", CALL_PUT_UNUSUAL_ACTIVITY_QUERY),
        ("Highest Volume/Open Interest Ratio Contracts", build_highest_volume_oi_ratio_query(limit)),
        ("Intraday Unusual Activity Count By Hour", INTRADAY_UNUSUAL_ACTIVITY_QUERY),
        ("Top Symbols By Total Volume", build_top_symbols_by_volume_query(limit)),
    ]

    for title, query in queries:
        columns, rows = run_query(query)
        print_results(title, columns, rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run warehouse analytics queries against local PostgreSQL.")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    run_analytics(limit=args.limit)


if __name__ == "__main__":
    main()
