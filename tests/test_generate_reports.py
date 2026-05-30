from __future__ import annotations

from src.reporting.generate_reports import (
    get_flag_distribution,
    get_option_type_summary,
    get_symbol_summary,
    get_top_unusual_contracts,
)


def make_enriched_event(
    *,
    symbol: str = "SPY",
    contract_symbol: str = "SPY_20260619_530_C",
    option_type: str = "CALL",
    volume: int = 100,
    open_interest: int = 1000,
    implied_volatility: float = 0.25,
    unusual_activity_score: int = 0,
    unusual_activity_flags: list[str] | None = None,
    volume_open_interest_ratio: float | None = 0.1,
) -> dict:
    return {
        "event_id": "evt_123",
        "symbol": symbol,
        "contract_symbol": contract_symbol,
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
        "event_timestamp": "2026-05-29T13:45:00",
        "source": "simulated",
        "unusual_activity_flags": unusual_activity_flags or [],
        "unusual_activity_score": unusual_activity_score,
        "volume_open_interest_ratio": volume_open_interest_ratio,
    }


def test_top_unusual_contracts_only_includes_records_with_score_above_zero() -> None:
    records = [
        make_enriched_event(contract_symbol="A", unusual_activity_score=0),
        make_enriched_event(contract_symbol="B", unusual_activity_score=1, unusual_activity_flags=["HIGH_IV"]),
    ]

    result = get_top_unusual_contracts(records)

    assert len(result) == 1
    assert result[0]["contract_symbol"] == "B"


def test_top_unusual_contracts_sorts_by_score_then_volume() -> None:
    records = [
        make_enriched_event(contract_symbol="LOW_SCORE", unusual_activity_score=1, volume=9000, unusual_activity_flags=["HIGH_VOLUME"]),
        make_enriched_event(contract_symbol="HIGH_SCORE_LOW_VOLUME", unusual_activity_score=2, volume=100, unusual_activity_flags=["HIGH_IV", "HIGH_VOLUME"]),
        make_enriched_event(contract_symbol="HIGH_SCORE_HIGH_VOLUME", unusual_activity_score=2, volume=500, unusual_activity_flags=["HIGH_IV", "HIGH_VOLUME"]),
    ]

    result = get_top_unusual_contracts(records)

    assert [row["contract_symbol"] for row in result[:3]] == [
        "HIGH_SCORE_HIGH_VOLUME",
        "HIGH_SCORE_LOW_VOLUME",
        "LOW_SCORE",
    ]


def test_symbol_summary_calculates_total_events_and_unusual_events_correctly() -> None:
    records = [
        make_enriched_event(symbol="SPY", unusual_activity_score=0),
        make_enriched_event(symbol="SPY", unusual_activity_score=1, unusual_activity_flags=["HIGH_IV"]),
        make_enriched_event(symbol="QQQ", unusual_activity_score=1, unusual_activity_flags=["HIGH_VOLUME"]),
    ]

    result = get_symbol_summary(records)
    spy_row = next(row for row in result if row["symbol"] == "SPY")

    assert spy_row["total_events"] == 2
    assert spy_row["unusual_events"] == 1


def test_symbol_summary_calculates_unusual_event_pct_correctly() -> None:
    records = [
        make_enriched_event(symbol="SPY", unusual_activity_score=0),
        make_enriched_event(symbol="SPY", unusual_activity_score=1, unusual_activity_flags=["HIGH_IV"]),
        make_enriched_event(symbol="SPY", unusual_activity_score=1, unusual_activity_flags=["HIGH_VOLUME"]),
        make_enriched_event(symbol="SPY", unusual_activity_score=0),
    ]

    result = get_symbol_summary(records)

    assert result[0]["unusual_event_pct"] == 0.5


def test_flag_distribution_counts_flags_correctly() -> None:
    records = [
        make_enriched_event(unusual_activity_score=2, unusual_activity_flags=["HIGH_IV", "HIGH_VOLUME"]),
        make_enriched_event(unusual_activity_score=1, unusual_activity_flags=["HIGH_IV"]),
    ]

    result = get_flag_distribution(records)

    assert result == [
        {"flag": "HIGH_IV", "count": 2},
        {"flag": "HIGH_VOLUME", "count": 1},
    ]


def test_option_type_summary_groups_call_and_put_correctly() -> None:
    records = [
        make_enriched_event(option_type="CALL", unusual_activity_score=1, unusual_activity_flags=["HIGH_IV"]),
        make_enriched_event(option_type="CALL", unusual_activity_score=0),
        make_enriched_event(option_type="PUT", unusual_activity_score=1, unusual_activity_flags=["HIGH_VOLUME"]),
    ]

    result = get_option_type_summary(records)

    assert result == [
        {
            "option_type": "CALL",
            "total_events": 2,
            "unusual_events": 1,
            "unusual_event_pct": 0.5,
            "total_volume": 200,
            "avg_implied_volatility": 0.25,
            "avg_unusual_activity_score": 0.5,
        },
        {
            "option_type": "PUT",
            "total_events": 1,
            "unusual_events": 1,
            "unusual_event_pct": 1.0,
            "total_volume": 100,
            "avg_implied_volatility": 0.25,
            "avg_unusual_activity_score": 1.0,
        },
    ]


def test_report_functions_handle_empty_input_without_crashing() -> None:
    assert get_top_unusual_contracts([]) == []
    assert get_symbol_summary([]) == []
    assert get_flag_distribution([]) == []
    assert get_option_type_summary([]) == []
