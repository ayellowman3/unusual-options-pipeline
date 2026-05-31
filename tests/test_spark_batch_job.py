from __future__ import annotations

import pytest

pyspark = pytest.importorskip("pyspark")
from pyspark.errors import PySparkRuntimeError

from src.spark.spark_batch_job import (
    create_spark_session,
    get_flag_summary,
    get_option_type_summary,
    get_symbol_daily_summary,
    get_unusual_events,
    transform_events,
)


@pytest.fixture(scope="module")
def spark():
    try:
        session = create_spark_session("UnusualOptionsSparkBatchTests")
    except PySparkRuntimeError as exc:
        pytest.skip(f"Spark session could not be started in this environment: {exc}")
    yield session
    session.stop()


@pytest.fixture
def sample_df(spark):
    records = [
        {
            "event_id": "evt_1",
            "symbol": "SPY",
            "contract_symbol": "SPY_20260619_530_C",
            "expiration_date": "2026-06-19",
            "strike": 530.0,
            "option_type": "CALL",
            "volume": 6000,
            "open_interest": 3000,
            "implied_volatility": 0.9,
            "unusual_activity_score": 3,
            "volume_open_interest_ratio": 2.0,
            "underlying_price": 528.1,
            "event_timestamp": "2026-05-29T13:45:00+00:00",
            "unusual_activity_flags": ["HIGH_VOLUME", "HIGH_IV", "VOLUME_EXCEEDS_OPEN_INTEREST"],
        },
        {
            "event_id": "evt_2",
            "symbol": "SPY",
            "contract_symbol": "SPY_20260619_520_P",
            "expiration_date": "2026-06-19",
            "strike": 520.0,
            "option_type": "PUT",
            "volume": 100,
            "open_interest": 2000,
            "implied_volatility": 0.2,
            "unusual_activity_score": 0,
            "volume_open_interest_ratio": 0.05,
            "underlying_price": 528.1,
            "event_timestamp": "2026-05-29T14:15:00+00:00",
            "unusual_activity_flags": [],
        },
        {
            "event_id": "evt_3",
            "symbol": "QQQ",
            "contract_symbol": "QQQ_20260619_460_C",
            "expiration_date": "2026-06-19",
            "strike": 460.0,
            "option_type": "CALL",
            "volume": 500,
            "open_interest": 1000,
            "implied_volatility": 0.8,
            "unusual_activity_score": 1,
            "volume_open_interest_ratio": 0.5,
            "underlying_price": 460.0,
            "event_timestamp": "2026-05-30T09:00:00+00:00",
            "unusual_activity_flags": ["HIGH_IV"],
        },
    ]
    return spark.createDataFrame(records)


def test_transform_events_adds_event_date_and_event_hour(sample_df) -> None:
    transformed = transform_events(sample_df)
    row = transformed.select("event_date", "event_hour").first()

    assert str(row.event_date) == "2026-05-29"
    assert row.event_hour == 13


def test_get_unusual_events_filters_correctly(sample_df) -> None:
    transformed = transform_events(sample_df)

    assert get_unusual_events(transformed).count() == 2


def test_get_symbol_daily_summary_calculates_unusual_events_correctly(sample_df) -> None:
    transformed = transform_events(sample_df)
    rows = get_symbol_daily_summary(transformed).collect()
    spy_row = next(row for row in rows if row.symbol == "SPY")

    assert spy_row.total_events == 2
    assert spy_row.unusual_events == 1
    assert float(spy_row.unusual_event_pct) == 0.5


def test_get_flag_summary_counts_exploded_flags_correctly(sample_df) -> None:
    transformed = transform_events(sample_df)
    rows = get_flag_summary(transformed).collect()
    result = {row.flag: row.flag_count for row in rows}

    assert result == {
        "HIGH_IV": 2,
        "HIGH_VOLUME": 1,
        "VOLUME_EXCEEDS_OPEN_INTEREST": 1,
    }


def test_get_option_type_summary_groups_call_and_put_correctly(sample_df) -> None:
    transformed = transform_events(sample_df)
    rows = get_option_type_summary(transformed).collect()
    result = {row.option_type: row for row in rows}

    assert result["CALL"].total_events == 2
    assert result["CALL"].unusual_events == 2
    assert float(result["CALL"].unusual_event_pct) == 1.0
    assert result["PUT"].total_events == 1
    assert result["PUT"].unusual_events == 0
    assert float(result["PUT"].unusual_event_pct) == 0.0
