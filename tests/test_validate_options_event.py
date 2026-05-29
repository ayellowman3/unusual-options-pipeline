from __future__ import annotations

from src.validation.validate_options_event import validate_options_event


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


def test_valid_event_has_no_errors() -> None:
    assert validate_options_event(make_valid_event()) == []


def test_missing_required_field_fails_validation() -> None:
    event = make_valid_event()
    del event["symbol"]

    errors = validate_options_event(event)

    assert "Missing required field: symbol" in errors


def test_invalid_option_type_fails_validation() -> None:
    event = make_valid_event()
    event["option_type"] = "SELL"

    errors = validate_options_event(event)

    assert "option_type must be one of {'CALL', 'PUT'}" in errors


def test_negative_volume_fails_validation() -> None:
    event = make_valid_event()
    event["volume"] = -1

    errors = validate_options_event(event)

    assert "volume cannot be negative" in errors


def test_bid_greater_than_ask_fails_validation() -> None:
    event = make_valid_event()
    event["bid"] = 5.0
    event["ask"] = 4.0

    errors = validate_options_event(event)

    assert "bid cannot be greater than ask" in errors


def test_invalid_event_timestamp_fails_validation() -> None:
    event = make_valid_event()
    event["event_timestamp"] = "not-a-timestamp"

    errors = validate_options_event(event)

    assert "event_timestamp must be a valid ISO datetime" in errors
