from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def read_jsonl(input_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            records.append(json.loads(stripped_line))

    return records


def get_connection():
    import psycopg2

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "unusual_options"),
        user=os.getenv("POSTGRES_USER", "unusual_user"),
        password=os.getenv("POSTGRES_PASSWORD", "unusual_password"),
    )


def execute_schema(schema_path: Path) -> None:
    schema_sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)


def get_unique_symbols(records: list[dict[str, Any]]) -> list[str]:
    return sorted({record["symbol"] for record in records})


def get_unique_contracts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_contracts: dict[str, dict[str, Any]] = {}

    for record in records:
        contract_symbol = record["contract_symbol"]
        if contract_symbol in unique_contracts:
            continue
        unique_contracts[contract_symbol] = {
            "contract_symbol": contract_symbol,
            "symbol": record["symbol"],
            "option_type": record["option_type"],
            "strike": record["strike"],
            "expiration_date": record["expiration_date"],
        }

    return list(unique_contracts.values())


def get_unusual_activity_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for record in records:
        for flag in record.get("unusual_activity_flags", []):
            rows.append(
                {
                    "event_id": record["event_id"],
                    "contract_symbol": record["contract_symbol"],
                    "symbol": record["symbol"],
                    "flag": flag,
                    "event_timestamp": record["event_timestamp"],
                }
            )

    return rows


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_iso_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def load_dim_symbol(records: list[dict[str, Any]]) -> int:
    rows = [(symbol,) for symbol in get_unique_symbols(records)]
    if not rows:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO dim_symbol (symbol)
                VALUES (%s)
                ON CONFLICT (symbol) DO NOTHING
                """,
                rows,
            )
            return cursor.rowcount


def load_dim_option_contract(records: list[dict[str, Any]]) -> int:
    contracts = get_unique_contracts(records)
    rows = [
        (
            contract["contract_symbol"],
            contract["symbol"],
            contract["option_type"],
            contract["strike"],
            _parse_iso_date(contract["expiration_date"]),
        )
        for contract in contracts
    ]
    if not rows:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO dim_option_contract (
                    contract_symbol,
                    symbol,
                    option_type,
                    strike,
                    expiration_date
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (contract_symbol) DO NOTHING
                """,
                rows,
            )
            return cursor.rowcount


def load_fact_options_event(records: list[dict[str, Any]]) -> int:
    rows = [
        (
            record["event_id"],
            record["contract_symbol"],
            record["symbol"],
            record["option_type"],
            record["strike"],
            _parse_iso_date(record["expiration_date"]),
            record["bid"],
            record["ask"],
            record["last_price"],
            record["volume"],
            record["open_interest"],
            record["volume_open_interest_ratio"],
            record["implied_volatility"],
            record["delta"],
            record["underlying_price"],
            record["unusual_activity_score"],
            _parse_iso_timestamp(record["event_timestamp"]),
            record["source"],
        )
        for record in records
    ]
    if not rows:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO fact_options_event (
                    event_id,
                    contract_symbol,
                    symbol,
                    option_type,
                    strike,
                    expiration_date,
                    bid,
                    ask,
                    last_price,
                    volume,
                    open_interest,
                    volume_open_interest_ratio,
                    implied_volatility,
                    delta,
                    underlying_price,
                    unusual_activity_score,
                    event_timestamp,
                    source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                rows,
            )
            return cursor.rowcount


def load_fact_unusual_activity(records: list[dict[str, Any]]) -> int:
    activity_rows = get_unusual_activity_rows(records)
    rows = [
        (
            row["event_id"],
            row["contract_symbol"],
            row["symbol"],
            row["flag"],
            _parse_iso_timestamp(row["event_timestamp"]),
        )
        for row in activity_rows
    ]
    if not rows:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO fact_unusual_activity (
                    event_id,
                    contract_symbol,
                    symbol,
                    flag,
                    event_timestamp
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (event_id, flag) DO NOTHING
                """,
                rows,
            )
            return cursor.rowcount


def load_warehouse(input_path: Path, schema_path: Path, reset_schema: bool = False) -> None:
    records = read_jsonl(input_path)

    if reset_schema:
        execute_schema(schema_path)

    inserted_symbols = load_dim_symbol(records)
    inserted_contracts = load_dim_option_contract(records)
    inserted_events = load_fact_options_event(records)
    inserted_flags = load_fact_unusual_activity(records)

    print(f"Records read: {len(records)}")
    print(f"dim_symbol rows inserted: {inserted_symbols}")
    print(f"dim_option_contract rows inserted: {inserted_contracts}")
    print(f"fact_options_event rows inserted: {inserted_events}")
    print(f"fact_unusual_activity rows inserted: {inserted_flags}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load enriched options activity events into PostgreSQL.")
    parser.add_argument("--input", default="data/processed/options_events_enriched.jsonl")
    parser.add_argument("--schema", default="sql/schema.sql")
    parser.add_argument("--reset-schema", action="store_true")
    args = parser.parse_args()

    load_warehouse(
        input_path=Path(args.input),
        schema_path=Path(args.schema),
        reset_schema=args.reset_schema,
    )


if __name__ == "__main__":
    main()
