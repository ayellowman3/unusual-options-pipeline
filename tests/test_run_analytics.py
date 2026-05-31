from __future__ import annotations

from src.warehouse.run_analytics import (
    FLAG_DISTRIBUTION_QUERY,
    SYMBOL_UNUSUAL_ACTIVITY_QUERY,
    build_highest_volume_oi_ratio_query,
    build_top_symbols_by_volume_query,
    build_top_unusual_contracts_query,
    print_results,
)


def test_print_results_handles_empty_rows_without_crashing(capsys) -> None:
    print_results("Sample Report", ["symbol", "total_volume"], [])

    captured = capsys.readouterr()

    assert "Sample Report" in captured.out
    assert "symbol | total_volume" in captured.out
    assert "(no rows)" in captured.out


def test_query_strings_are_accessible() -> None:
    assert "FROM fact_unusual_activity" in FLAG_DISTRIBUTION_QUERY
    assert "FROM fact_options_event" in SYMBOL_UNUSUAL_ACTIVITY_QUERY


def test_limit_value_is_passed_into_query_generation() -> None:
    assert "LIMIT 10" in build_top_unusual_contracts_query(10)
    assert "LIMIT 7" in build_highest_volume_oi_ratio_query(7)
    assert "LIMIT 3" in build_top_symbols_by_volume_query(3)
