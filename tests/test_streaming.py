from __future__ import annotations

import json

from src.streaming import append_jsonl, format_event_summary
from src.streaming.stream_consumer import process_stream_event


def make_event(
    *,
    volume: int = 1200,
    open_interest: int = 8500,
    implied_volatility: float = 0.245,
    option_type: str = "CALL",
) -> dict:
    return {
        "event_id": "evt_123",
        "symbol": "SPY",
        "contract_symbol": "SPY_20260619_530_C",
        "expiration_date": "2026-06-19",
        "strike": 530.0,
        "option_type": option_type,
        "bid": 4.2,
        "ask": 4.5,
        "last_price": 4.35,
        "volume": volume,
        "open_interest": open_interest,
        "implied_volatility": implied_volatility,
        "delta": 0.54,
        "underlying_price": 528.1,
        "event_timestamp": "2026-05-29T13:45:00+00:00",
        "source": "simulated",
    }


def test_append_jsonl_writes_one_json_record_per_line(tmp_path) -> None:
    output_path = tmp_path / "stream.jsonl"

    append_jsonl({"event_id": "evt_1"}, output_path)
    append_jsonl({"event_id": "evt_2"}, output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert json.loads(lines[0]) == {"event_id": "evt_1"}
    assert json.loads(lines[1]) == {"event_id": "evt_2"}


def test_format_event_summary_includes_symbol_and_contract_symbol() -> None:
    summary = format_event_summary(make_event())

    assert "symbol=SPY" in summary
    assert "contract_symbol=SPY_20260619_530_C" in summary


def test_process_stream_event_returns_alert_for_valid_unusual_event() -> None:
    event = make_event(volume=6000, open_interest=3000, implied_volatility=0.9)

    alert_record, invalid_record = process_stream_event(event)

    assert invalid_record is None
    assert alert_record is not None
    assert alert_record["unusual_activity_score"] == 3


def test_process_stream_event_returns_no_alert_for_valid_normal_event() -> None:
    alert_record, invalid_record = process_stream_event(make_event())

    assert alert_record is None
    assert invalid_record is None


def test_process_stream_event_returns_invalid_record_for_invalid_event() -> None:
    event = make_event()
    event["volume"] = -5

    alert_record, invalid_record = process_stream_event(event)

    assert alert_record is None
    assert invalid_record is not None
    assert invalid_record["validation_errors"] == ["volume cannot be negative"]
