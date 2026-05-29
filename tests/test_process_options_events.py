from __future__ import annotations

from src.processing.process_options_events import enrich_event, get_unusual_activity_flags, process_events


def make_valid_event() -> dict:
    return {
        "event_id": "evt_123",
        "symbol": "SPY",
        "contract_symbol": "SPY_20260619_530_C",
        "expiration_date": "2026-06-19",
        "strike": 530.0,
        "option_type": "CALL",
        "bid": 4.2,
        "ask": 4.5,
        "last_price": 4.35,
        "volume": 1200,
        "open_interest": 8500,
        "implied_volatility": 0.245,
        "delta": 0.54,
        "underlying_price": 528.1,
        "event_timestamp": "2026-05-29T13:45:00",
        "source": "simulated",
    }


def test_high_volume_flag() -> None:
    event = make_valid_event()
    event["volume"] = 5000

    assert "HIGH_VOLUME" in get_unusual_activity_flags(event)


def test_volume_exceeds_open_interest_flag() -> None:
    event = make_valid_event()
    event["volume"] = 2000
    event["open_interest"] = 1000

    assert "VOLUME_EXCEEDS_OPEN_INTEREST" in get_unusual_activity_flags(event)


def test_high_iv_flag() -> None:
    event = make_valid_event()
    event["implied_volatility"] = 0.80

    assert "HIGH_IV" in get_unusual_activity_flags(event)


def test_event_with_no_flags_has_score_zero() -> None:
    enriched_event = enrich_event(make_valid_event())

    assert enriched_event["unusual_activity_flags"] == []
    assert enriched_event["unusual_activity_score"] == 0


def test_volume_open_interest_ratio_is_calculated_correctly() -> None:
    event = make_valid_event()
    event["volume"] = 333
    event["open_interest"] = 1000

    enriched_event = enrich_event(event)

    assert enriched_event["volume_open_interest_ratio"] == 0.333


def test_invalid_event_is_separated_into_invalid_records() -> None:
    valid_event = make_valid_event()
    invalid_event = make_valid_event()
    invalid_event["volume"] = -10

    valid_records, invalid_records = process_events([valid_event, invalid_event])

    assert len(valid_records) == 1
    assert len(invalid_records) == 1
    assert invalid_records[0]["validation_errors"] == ["volume cannot be negative"]


def test_valid_event_is_enriched_with_unusual_activity_fields() -> None:
    event = make_valid_event()
    event["volume"] = 9000
    event["open_interest"] = 4000
    event["implied_volatility"] = 0.95

    valid_records, invalid_records = process_events([event])

    assert invalid_records == []
    assert valid_records[0]["unusual_activity_flags"] == [
        "HIGH_VOLUME",
        "VOLUME_EXCEEDS_OPEN_INTEREST",
        "HIGH_IV",
    ]
    assert valid_records[0]["unusual_activity_score"] == 3
