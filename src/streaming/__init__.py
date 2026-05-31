from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def append_jsonl(record: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def format_event_summary(event: dict[str, Any]) -> str:
    return (
        f"event_id={event.get('event_id')} "
        f"symbol={event.get('symbol')} "
        f"contract_symbol={event.get('contract_symbol')} "
        f"volume={event.get('volume')} "
        f"open_interest={event.get('open_interest')} "
        f"implied_volatility={event.get('implied_volatility')}"
    )
