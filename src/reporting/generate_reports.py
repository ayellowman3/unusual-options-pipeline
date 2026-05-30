from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
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


def write_csv(records: list[dict[str, Any]], output_path: Path, fieldnames: list[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def get_top_unusual_contracts(records: list[dict[str, Any]], limit: int = 25) -> list[dict[str, Any]]:
    unusual_records = [record for record in records if record.get("unusual_activity_score", 0) > 0]
    sorted_records = sorted(
        unusual_records,
        key=lambda record: (
            -record["unusual_activity_score"],
            -record["volume"],
            -(record.get("volume_open_interest_ratio") or 0),
        ),
    )

    top_records: list[dict[str, Any]] = []
    for record in sorted_records[:limit]:
        top_records.append(
            {
                "contract_symbol": record["contract_symbol"],
                "symbol": record["symbol"],
                "option_type": record["option_type"],
                "strike": record["strike"],
                "expiration_date": record["expiration_date"],
                "volume": record["volume"],
                "open_interest": record["open_interest"],
                "volume_open_interest_ratio": record["volume_open_interest_ratio"],
                "implied_volatility": record["implied_volatility"],
                "unusual_activity_score": record["unusual_activity_score"],
                "unusual_activity_flags": "|".join(record["unusual_activity_flags"]),
            }
        )

    return top_records


def get_symbol_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped_records: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "total_events": 0,
            "unusual_events": 0,
            "total_volume": 0,
            "iv_sum": 0.0,
            "score_sum": 0.0,
        }
    )

    for record in records:
        group = grouped_records[record["symbol"]]
        group["total_events"] += 1
        group["unusual_events"] += 1 if record["unusual_activity_score"] > 0 else 0
        group["total_volume"] += record["volume"]
        group["iv_sum"] += record["implied_volatility"]
        group["score_sum"] += record["unusual_activity_score"]

    summary_rows: list[dict[str, Any]] = []
    for symbol, group in grouped_records.items():
        total_events = int(group["total_events"])
        unusual_events = int(group["unusual_events"])
        summary_rows.append(
            {
                "symbol": symbol,
                "total_events": total_events,
                "unusual_events": unusual_events,
                "unusual_event_pct": round(unusual_events / total_events, 4) if total_events else 0.0,
                "total_volume": int(group["total_volume"]),
                "avg_implied_volatility": round(group["iv_sum"] / total_events, 4) if total_events else 0.0,
                "avg_unusual_activity_score": round(group["score_sum"] / total_events, 4) if total_events else 0.0,
            }
        )

    return sorted(summary_rows, key=lambda row: (-row["unusual_events"], -row["total_volume"]))


def get_flag_distribution(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flag_counts: dict[str, int] = defaultdict(int)

    for record in records:
        for flag in record.get("unusual_activity_flags", []):
            flag_counts[flag] += 1

    distribution_rows = [{"flag": flag, "count": count} for flag, count in flag_counts.items()]
    return sorted(distribution_rows, key=lambda row: (-row["count"], row["flag"]))


def get_option_type_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped_records: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "total_events": 0,
            "unusual_events": 0,
            "total_volume": 0,
            "iv_sum": 0.0,
            "score_sum": 0.0,
        }
    )

    for record in records:
        group = grouped_records[record["option_type"]]
        group["total_events"] += 1
        group["unusual_events"] += 1 if record["unusual_activity_score"] > 0 else 0
        group["total_volume"] += record["volume"]
        group["iv_sum"] += record["implied_volatility"]
        group["score_sum"] += record["unusual_activity_score"]

    summary_rows: list[dict[str, Any]] = []
    for option_type, group in grouped_records.items():
        total_events = int(group["total_events"])
        unusual_events = int(group["unusual_events"])
        summary_rows.append(
            {
                "option_type": option_type,
                "total_events": total_events,
                "unusual_events": unusual_events,
                "unusual_event_pct": round(unusual_events / total_events, 4) if total_events else 0.0,
                "total_volume": int(group["total_volume"]),
                "avg_implied_volatility": round(group["iv_sum"] / total_events, 4) if total_events else 0.0,
                "avg_unusual_activity_score": round(group["score_sum"] / total_events, 4) if total_events else 0.0,
            }
        )

    return sorted(summary_rows, key=lambda row: row["option_type"])


def generate_reports(input_path: Path, output_dir: Path) -> None:
    records = read_jsonl(input_path)

    top_unusual_contracts = get_top_unusual_contracts(records)
    symbol_summary = get_symbol_summary(records)
    flag_distribution = get_flag_distribution(records)
    option_type_summary = get_option_type_summary(records)

    write_csv(
        top_unusual_contracts,
        output_dir / "top_unusual_contracts.csv",
        [
            "contract_symbol",
            "symbol",
            "option_type",
            "strike",
            "expiration_date",
            "volume",
            "open_interest",
            "volume_open_interest_ratio",
            "implied_volatility",
            "unusual_activity_score",
            "unusual_activity_flags",
        ],
    )
    write_csv(
        symbol_summary,
        output_dir / "symbol_summary.csv",
        [
            "symbol",
            "total_events",
            "unusual_events",
            "unusual_event_pct",
            "total_volume",
            "avg_implied_volatility",
            "avg_unusual_activity_score",
        ],
    )
    write_csv(
        flag_distribution,
        output_dir / "flag_distribution.csv",
        ["flag", "count"],
    )
    write_csv(
        option_type_summary,
        output_dir / "option_type_summary.csv",
        [
            "option_type",
            "total_events",
            "unusual_events",
            "unusual_event_pct",
            "total_volume",
            "avg_implied_volatility",
            "avg_unusual_activity_score",
        ],
    )

    print(f"Total records read: {len(records)}")
    print(f"Number of top unusual contracts written: {len(top_unusual_contracts)}")
    print(f"Number of symbol summary rows written: {len(symbol_summary)}")
    print(f"Number of flag distribution rows written: {len(flag_distribution)}")
    print(f"Number of option type summary rows written: {len(option_type_summary)}")
    print(f"Output directory: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CSV reports from enriched options activity events.")
    parser.add_argument("--input", default="data/processed/options_events_enriched.jsonl")
    parser.add_argument("--output-dir", default="data/processed/reports")
    args = parser.parse_args()

    generate_reports(Path(args.input), Path(args.output_dir))


if __name__ == "__main__":
    main()
