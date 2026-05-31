from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.process_options_events import enrich_event
from src.streaming import append_jsonl
from src.validation.validate_options_event import validate_options_event


DEFAULT_INVALID_OUTPUT = Path("data/stream/invalid_stream_events.jsonl")


def process_stream_event(event: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    validation_errors = validate_options_event(event)
    if validation_errors:
        invalid_record = dict(event)
        invalid_record["validation_errors"] = validation_errors
        return None, invalid_record

    enriched_event = enrich_event(event)
    if enriched_event["unusual_activity_score"] > 0:
        return enriched_event, None

    return None, None


def format_processing_summary(
    event: dict[str, Any],
    is_valid: bool,
    unusual_activity_score: int,
    flags: list[str],
) -> str:
    flag_text = "|".join(flags) if flags else "NONE"
    status = "valid" if is_valid else "invalid"
    return (
        f"event_id={event.get('event_id')} "
        f"symbol={event.get('symbol')} "
        f"status={status} "
        f"unusual_activity_score={unusual_activity_score} "
        f"flags={flag_text}"
    )


def consume_stream(
    input_path: Path,
    alerts_output_path: Path,
    invalid_output_path: Path,
    max_events: int | None,
    sleep_seconds: float,
) -> None:
    processed_events = 0
    file_position = 0

    while max_events is None or processed_events < max_events:
        if not input_path.exists():
            time.sleep(sleep_seconds)
            continue

        with input_path.open("r", encoding="utf-8") as file:
            file.seek(file_position)
            new_lines = file.readlines()
            file_position = file.tell()

        if not new_lines:
            time.sleep(sleep_seconds)
            continue

        for line in new_lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            event = json.loads(stripped_line)
            alert_record, invalid_record = process_stream_event(event)

            if invalid_record is not None:
                append_jsonl(invalid_record, invalid_output_path)
                print(
                    format_processing_summary(
                        event=event,
                        is_valid=False,
                        unusual_activity_score=0,
                        flags=[],
                    )
                )
            elif alert_record is not None:
                append_jsonl(alert_record, alerts_output_path)
                print(
                    format_processing_summary(
                        event=event,
                        is_valid=True,
                        unusual_activity_score=alert_record["unusual_activity_score"],
                        flags=alert_record["unusual_activity_flags"],
                    )
                )
            else:
                print(
                    format_processing_summary(
                        event=event,
                        is_valid=True,
                        unusual_activity_score=0,
                        flags=[],
                    )
                )

            processed_events += 1
            if max_events is not None and processed_events >= max_events:
                return


def main() -> None:
    parser = argparse.ArgumentParser(description="Consume a local JSONL event stream and emit unusual activity alerts.")
    parser.add_argument("--input", default="data/stream/options_events_stream.jsonl")
    parser.add_argument("--alerts-output", default="data/stream/unusual_activity_alerts.jsonl")
    parser.add_argument("--max-events", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    args = parser.parse_args()

    consume_stream(
        input_path=Path(args.input),
        alerts_output_path=Path(args.alerts_output),
        invalid_output_path=DEFAULT_INVALID_OUTPUT,
        max_events=args.max_events,
        sleep_seconds=args.sleep_seconds,
    )


if __name__ == "__main__":
    main()
