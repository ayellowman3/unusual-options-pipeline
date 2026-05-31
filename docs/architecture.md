# Architecture

## Overview

This project models a local end-to-end data pipeline for unusual options activity. It is intentionally lightweight, but each layer maps to a common production data engineering pattern.

## End-To-End Flow

```text
Raw data generation
  -> validation
  -> enrichment
  -> reporting
  -> warehouse loading
  -> SQL analytics
  -> streaming simulation
  -> Spark batch outputs
```

## Local Pipeline Diagram

```text
[Generator]
  src/generator/generate_options_events.py
        |
        v
[Raw JSONL]
  data/raw/options_events.jsonl
        |
        v
[Validation + Enrichment]
  src/processing/process_options_events.py
        |
        +--> data/processed/options_events_invalid.jsonl
        |
        v
[Enriched JSONL]
  data/processed/options_events_enriched.jsonl
        |
        +--> [CSV Reporting]
        |      src/reporting/generate_reports.py
        |      -> data/processed/reports/
        |
        +--> [Warehouse Load]
        |      src/warehouse/load_warehouse.py
        |      -> PostgreSQL
        |
        +--> [Spark Batch]
               src/spark/spark_batch_job.py
               -> data/spark_output/
```

## Streaming Simulation Diagram

```text
[Stream Producer]
  src/streaming/stream_producer.py
        |
        v
[Stream File]
  data/stream/options_events_stream.jsonl
        |
        v
[Stream Consumer]
  src/streaming/stream_consumer.py
        |
        +--> data/stream/unusual_activity_alerts.jsonl
        |
        +--> data/stream/invalid_stream_events.jsonl
```

## Layer Descriptions

### Raw Data Generation

The generator produces synthetic options events with realistic-looking fields such as symbol, contract, bid/ask, implied volatility, and volume. This gives the rest of the pipeline a reproducible event stream without relying on a live market data source.

### Validation

Validation checks required fields, type assumptions, price relationships, positive numeric constraints, and ISO date/timestamp correctness. Invalid records are separated instead of silently discarded.

### Enrichment

Valid events are enriched with:
- `unusual_activity_flags`
- `unusual_activity_score`
- `volume_open_interest_ratio`

This converts raw events into a curated analytical dataset.

### Reporting

CSV reports summarize:
- top unusual contracts
- symbol-level activity
- flag distribution
- option type behavior

This layer is useful for analyst-style consumption and quick business review.

### Warehouse Loading

The PostgreSQL warehouse separates reusable dimensions from analytical facts:
- `dim_symbol`
- `dim_option_contract`
- `fact_options_event`
- `fact_unusual_activity`

The load process is idempotent and supports rerunnable local development.

### SQL Analytics

Warehouse analytics provide queryable summaries such as:
- top unusual contracts
- unusual activity by symbol
- call/put comparisons
- flag distribution
- intraday activity trends

### Streaming Simulation

The local JSONL stream models producer/consumer behavior without requiring Kafka. It is useful for discussing event-driven ingestion, alerting, and replay concepts in interviews.

### Spark Batch Outputs

The Spark layer demonstrates how the enriched dataset can be processed in a distributed-style engine and written to Parquet for scalable analytical storage.
