# unusual-options-pipeline

`unusual-options-pipeline` is an interview-prep project for a Capital One Lead Data Engineer-style role. It models an end-to-end pipeline for unusual options activity, starting from synthetic event generation and moving through validation, enrichment, reporting, warehouse loading, SQL analytics, streaming simulation, and PySpark batch processing.

## Project Purpose

This project was built to demonstrate the kind of system design and implementation thinking expected from a senior data engineer:
- designing a layered pipeline instead of a one-off script
- separating raw, validated, enriched, curated, and analytical views of data
- modeling both batch and streaming-style workflows
- thinking about idempotency, replay, observability, and production mappings
- showing fluency across Python, SQL, warehouse design, and Spark

The domain is unusual options activity because it creates realistic event-driven data with clear opportunities for validation, signal generation, aggregation, and alerting.

## Tech Stack

- Python 3
- JSONL for local raw and stream-style event transport
- `pytest` for unit testing
- PostgreSQL for local warehouse modeling
- SQL for schema and analytical queries
- PySpark for distributed-style batch processing concepts
- Parquet for Spark analytical outputs

## Local Architecture

The local architecture is intentionally simple but mirrors production patterns:

```text
Synthetic Options Events
  -> Raw JSONL
  -> Validation
  -> Enrichment / Unusual Activity Scoring
  -> CSV Reporting
  -> PostgreSQL Warehouse
  -> SQL Analytics
  -> Streaming Simulation (producer / consumer / alerts)
  -> PySpark Batch Outputs
```

Core implementation areas:
- `src/generator/`: synthetic event generation
- `src/validation/`: schema and business-rule validation
- `src/processing/`: enrichment and unusual activity scoring
- `src/reporting/`: CSV summary generation
- `src/warehouse/`: warehouse loading and SQL analytics runner
- `src/streaming/`: local producer/consumer simulation
- `src/spark/`: Spark batch transformations and Parquet outputs

## Batch Pipeline Flow

The batch flow starts with generated raw events and progressively curates them:

1. Generate synthetic options events into `data/raw/options_events.jsonl`
2. Validate each event and quarantine invalid records
3. Enrich valid records with unusual activity flags and scores
4. Produce analyst-friendly CSV reports
5. Load curated records into PostgreSQL dimension/fact tables
6. Run SQL analytics against the warehouse
7. Optionally process the enriched dataset with PySpark for distributed-style summaries

## Streaming Simulation Flow

The streaming flow is a lightweight local simulation of Kafka/Kinesis behavior:

1. A producer generates events one at a time
2. Each event is appended to a JSONL stream file
3. A consumer tails the stream file for new events
4. The consumer validates and enriches each event
5. Unusual events are appended to an alerts file
6. Invalid events are quarantined to a separate invalid-stream file

This gives you an interview-friendly way to discuss event-driven systems before introducing Kafka, MSK, or Kinesis.

## Warehouse Model

The warehouse layer uses a simple dimensional pattern:

- `dim_symbol`
  - unique symbols
- `dim_option_contract`
  - unique option contracts by contract symbol, option type, strike, expiration
- `fact_options_event`
  - enriched options activity events with metrics and unusual activity score
- `fact_unusual_activity`
  - one row per event flag for analytical flexibility

This structure supports both operational-style querying and downstream analytics.

## Spark Batch Layer

The Spark layer reads enriched JSONL events and writes Parquet outputs for:
- unusual events
- symbol daily summary
- flag summary
- option type summary

Locally this runs in single-machine Spark mode. In production, the same pattern maps naturally to EMR, Glue, Databricks, or Spark on Kubernetes.

## How To Run The Full Pipeline

### 1. Generate Raw Events

```bash
python3 src/generator/generate_options_events.py --count 1000
```

### 2. Validate And Enrich Events

```bash
python3 src/processing/process_options_events.py \
  --input data/raw/options_events.jsonl \
  --valid-output data/processed/options_events_enriched.jsonl \
  --invalid-output data/processed/options_events_invalid.jsonl
```

### 3. Generate CSV Reports

```bash
python3 src/reporting/generate_reports.py \
  --input data/processed/options_events_enriched.jsonl \
  --output-dir data/processed/reports
```

### 4. Load The Warehouse

```bash
python3 src/warehouse/load_warehouse.py \
  --input data/processed/options_events_enriched.jsonl \
  --schema sql/schema.sql \
  --reset-schema
```

### 5. Run SQL Analytics

```bash
python3 src/warehouse/run_analytics.py
```

### 6. Run Streaming Simulation

Consumer terminal:

```bash
python3 src/streaming/stream_consumer.py \
  --input data/stream/options_events_stream.jsonl \
  --alerts-output data/stream/unusual_activity_alerts.jsonl \
  --max-events 100
```

Producer terminal:

```bash
python3 src/streaming/stream_producer.py \
  --output data/stream/options_events_stream.jsonl \
  --count 100 \
  --sleep-seconds 0.25
```

Note:
- This local JSONL stream simulates Kafka/Kinesis for interview practice.
- In production, replace the JSONL stream with Kafka, AWS MSK, or Kinesis.

### 7. Run Spark Batch Processing

```bash
python3 src/spark/spark_batch_job.py \
  --input data/processed/options_events_enriched.jsonl \
  --output-dir data/spark_output
```

Note:
- Locally this runs in single-machine Spark mode.
- In production, this maps to AWS EMR, AWS Glue, Databricks, or Spark on Kubernetes.

## How To Run Tests

```bash
pytest
```

## Why This Maps Well To A Capital One Lead Data Engineer Role

This project demonstrates the kinds of responsibilities a Lead Data Engineer is expected to handle:
- building reliable ingestion and transformation pipelines
- defining validation and data quality controls
- designing dimensional warehouse models and analytical access patterns
- thinking in both batch and streaming paradigms
- implementing repeatable, testable, modular code
- documenting architectural tradeoffs and production evolution paths

It also creates a strong interview narrative: the project is small enough to explain clearly, but broad enough to discuss design decisions, scalability, operational readiness, and ownership.

## Additional Documentation

- [Architecture](docs/architecture.md)
- [AWS Mapping](docs/aws_mapping.md)
- [Tradeoffs](docs/tradeoffs.md)
- [Interview Walkthrough](docs/interview_walkthrough.md)
