from __future__ import annotations

from datetime import date, datetime
from typing import Any


REQUIRED_FIELDS = {
    "event_id",
    "symbol",
    "contract_symbol",
    "expiration_date",
    "strike",
    "option_type",
    "bid",
    "ask",
    "last_price",
    "volume",
    "open_interest",
    "implied_volatility",
    "delta",
    "underlying_price",
    "event_timestamp",
    "source",
}

VALID_OPTION_TYPES = {"CALL", "PUT"}


def parse_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def parse_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def validate_options_event(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing_fields = sorted(field for field in REQUIRED_FIELDS if field not in event)
    for field in missing_fields:
        errors.append(f"Missing required field: {field}")

    if missing_fields:
        return errors

    if event["option_type"] not in VALID_OPTION_TYPES:
        errors.append("option_type must be one of {'CALL', 'PUT'}")

    if event["volume"] < 0:
        errors.append("volume cannot be negative")

    if event["open_interest"] < 0:
        errors.append("open_interest cannot be negative")

    if event["bid"] < 0:
        errors.append("bid cannot be negative")

    if event["ask"] < 0:
        errors.append("ask cannot be negative")

    if event["bid"] > event["ask"]:
        errors.append("bid cannot be greater than ask")

    if event["last_price"] < 0:
        errors.append("last_price cannot be negative")

    if event["strike"] <= 0:
        errors.append("strike must be positive")

    if event["underlying_price"] <= 0:
        errors.append("underlying_price must be positive")

    if event["implied_volatility"] <= 0:
        errors.append("implied_volatility must be positive")

    if not parse_iso_datetime(event["event_timestamp"]):
        errors.append("event_timestamp must be a valid ISO datetime")

    if not parse_iso_date(event["expiration_date"]):
        errors.append("expiration_date must be a valid ISO date")

    return errors


def is_valid_options_event(event: dict[str, Any]) -> bool:
    return not validate_options_event(event)
