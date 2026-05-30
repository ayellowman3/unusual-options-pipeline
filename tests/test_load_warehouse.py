from __future__ import annotations

import json

from src.warehouse.load_warehouse import (
    get_unique_contracts,
    get_unique_symbols,
    get_unusual_activity_rows,
    read_jsonl,
)


def make_enriched_event(
    *,
    event_id: str = "evt_123",
    symbol: str = "SPY",
    contract_symbol: str = "SPY_20260619_530_C",
    option_type: str = "CALL",
    unusual_activity_flags: list[str] | None = None,
) -> dict:
    return {
        "event_id": event_id,
        "symbol": symbol,
        "contract_symbol": contract_symbol,
        "expiration_date": "2026-06-19",
        "strike": 530.0,
        "option_type": option_type,
        "bid": 4.2,
        "ask": 4.5,
        "last_price": 4.35,
        "volume": 1200,
        "open_interest": 8500,
        "volume_open_interest_ratio": 0.1412,
        "implied_volatility": 0.245,
        "delta": 0.54,
        "underlying_price": 528.1,
        "unusual_activity_score": len(unusual_activity_flags or []),
        "unusual_activity_flags": unusual_activity_flags or [],
        "event_timestamp": "2026-05-29T13:45:00+00:00",
        "source": "simulated",
    }


def test_read_jsonl_reads_multiple_records(tmp_path) -> None:
    input_path = tmp_path / "sample.jsonl"
    records = [
        {"event_id": "evt_1", "symbol": "SPY"},
        {"event_id": "evt_2", "symbol": "QQQ"},
    ]
    input_path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    result = read_jsonl(input_path)

    assert result == records


def test_get_unique_symbols_derives_unique_symbols_correctly() -> None:
    records = [
        make_enriched_event(symbol="SPY"),
        make_enriched_event(event_id="evt_2", symbol="QQQ"),
        make_enriched_event(event_id="evt_3", symbol="SPY"),
    ]

    assert get_unique_symbols(records) == ["QQQ", "SPY"]


def test_get_unique_contracts_derives_unique_contracts_correctly() -> None:
    records = [
        make_enriched_event(contract_symbol="SPY_1", symbol="SPY"),
        make_enriched_event(event_id="evt_2", contract_symbol="SPY_1", symbol="SPY"),
        make_enriched_event(event_id="evt_3", contract_symbol="QQQ_1", symbol="QQQ", option_type="PUT"),
    ]

    result = get_unique_contracts(records)

    assert result == [
        {
            "contract_symbol": "SPY_1",
            "symbol": "SPY",
            "option_type": "CALL",
            "strike": 530.0,
            "expiration_date": "2026-06-19",
        },
        {
            "contract_symbol": "QQQ_1",
            "symbol": "QQQ",
            "option_type": "PUT",
            "strike": 530.0,
            "expiration_date": "2026-06-19",
        },
    ]


def test_get_unusual_activity_rows_derives_one_row_per_event_flag() -> None:
    records = [
        make_enriched_event(event_id="evt_1", unusual_activity_flags=["HIGH_VOLUME", "HIGH_IV"]),
        make_enriched_event(event_id="evt_2", unusual_activity_flags=["HIGH_IV"]),
    ]

    result = get_unusual_activity_rows(records)

    assert result == [
        {
            "event_id": "evt_1",
            "contract_symbol": "SPY_20260619_530_C",
            "symbol": "SPY",
            "flag": "HIGH_VOLUME",
            "event_timestamp": "2026-05-29T13:45:00+00:00",
        },
        {
            "event_id": "evt_1",
            "contract_symbol": "SPY_20260619_530_C",
            "symbol": "SPY",
            "flag": "HIGH_IV",
            "event_timestamp": "2026-05-29T13:45:00+00:00",
        },
        {
            "event_id": "evt_2",
            "contract_symbol": "SPY_20260619_530_C",
            "symbol": "SPY",
            "flag": "HIGH_IV",
            "event_timestamp": "2026-05-29T13:45:00+00:00",
        },
    ]


def test_get_unusual_activity_rows_returns_no_rows_for_events_with_no_flags() -> None:
    records = [
        make_enriched_event(unusual_activity_flags=[]),
        make_enriched_event(event_id="evt_2", unusual_activity_flags=[]),
    ]

    assert get_unusual_activity_rows(records) == []
