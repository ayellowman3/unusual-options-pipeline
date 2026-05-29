from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.validate_options_event import validate_options_event


def read_jsonl(input_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            records.append(json.loads(stripped_line))

    return records


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record) + "\n")


def get_unusual_activity_flags(event: dict[str, Any]) -> list[str]:
    flags: list[str] = []

    volume = event["volume"]
    open_interest = event["open_interest"]
    implied_volatility = event["implied_volatility"]

    if volume >= 5000:
        flags.append("HIGH_VOLUME")

    if open_interest > 0 and volume / open_interest >= 1.0:
        flags.append("VOLUME_EXCEEDS_OPEN_INTEREST")

    if implied_volatility >= 0.80:
        flags.append("HIGH_IV")

    return flags


def enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    enriched_event = dict(event)
    open_interest = enriched_event["open_interest"]
    ratio = None if open_interest == 0 else round(enriched_event["volume"] / open_interest, 4)
    flags = get_unusual_activity_flags(enriched_event)

    enriched_event["unusual_activity_flags"] = flags
    enriched_event["unusual_activity_score"] = len(flags)
    enriched_event["volume_open_interest_ratio"] = ratio

    return enriched_event


def process_events(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []

    for record in records:
        validation_errors = validate_options_event(record)
        if validation_errors:
            invalid_record = dict(record)
            invalid_record["validation_errors"] = validation_errors
            invalid_records.append(invalid_record)
            continue

        valid_records.append(enrich_event(record))

    return valid_records, invalid_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and enrich raw options activity events.")
    parser.add_argument("--input", default="data/raw/options_events.jsonl")
    parser.add_argument("--valid-output", default="data/processed/options_events_enriched.jsonl")
    parser.add_argument("--invalid-output", default="data/processed/options_events_invalid.jsonl")
    args = parser.parse_args()

    input_path = Path(args.input)
    valid_output_path = Path(args.valid_output)
    invalid_output_path = Path(args.invalid_output)

    records = read_jsonl(input_path)
    valid_records, invalid_records = process_events(records)

    write_jsonl(valid_records, valid_output_path)
    write_jsonl(invalid_records, invalid_output_path)

    unusual_activity_count = sum(1 for record in valid_records if record["unusual_activity_score"] > 0)

    print(f"Total records read: {len(records)}")
    print(f"Valid records written: {len(valid_records)}")
    print(f"Invalid records written: {len(invalid_records)}")
    print(f"Unusual activity records count: {unusual_activity_count}")


if __name__ == "__main__":
    main()
