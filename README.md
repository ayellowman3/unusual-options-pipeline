# unusual-options-pipeline

Local interview-prep pipeline for generating, validating, enriching, reporting on, and warehousing simulated unusual options activity events.

## Run The Full Pipeline

```bash
python3 src/generator/generate_options_events.py --count 1000

python3 src/processing/process_options_events.py \
  --input data/raw/options_events.jsonl \
  --valid-output data/processed/options_events_enriched.jsonl \
  --invalid-output data/processed/options_events_invalid.jsonl

python3 src/reporting/generate_reports.py \
  --input data/processed/options_events_enriched.jsonl \
  --output-dir data/processed/reports

python3 src/warehouse/load_warehouse.py \
  --input data/processed/options_events_enriched.jsonl \
  --schema sql/schema.sql \
  --reset-schema

python3 src/warehouse/run_analytics.py

pytest
```

## Streaming Simulation

This local JSONL stream simulates Kafka/Kinesis for interview practice.
In production, replace the JSONL stream with Kafka, AWS MSK, or Kinesis.

Terminal 1:

```bash
python3 src/streaming/stream_consumer.py \
  --input data/stream/options_events_stream.jsonl \
  --alerts-output data/stream/unusual_activity_alerts.jsonl \
  --max-events 100
```

Terminal 2:

```bash
python3 src/streaming/stream_producer.py \
  --output data/stream/options_events_stream.jsonl \
  --count 100 \
  --sleep-seconds 0.25
```
