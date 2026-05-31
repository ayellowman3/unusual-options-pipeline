from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generator.generate_options_events import generate_options_event
from src.streaming import append_jsonl, format_event_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Produce simulated options events into a local JSONL stream.")
    parser.add_argument("--output", default="data/stream/options_events_stream.jsonl")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    args = parser.parse_args()

    output_path = Path(args.output)

    for _ in range(args.count):
        event = generate_options_event()
        append_jsonl(event, output_path)
        print(format_event_summary(event))

        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()
