# AWS Mapping

## Local To AWS Mapping

- Local JSONL raw files -> S3 raw zone
- Python generator or API ingestion -> Lambda, ECS, or Glue Python shell
- Local stream JSONL -> Kinesis, MSK, or Kafka
- Stream consumer -> Lambda, ECS service, Flink, or Spark Structured Streaming
- Local processed JSONL -> S3 processed zone
- PostgreSQL -> Redshift or Snowflake
- PySpark local -> EMR, Glue, Databricks
- Local reports -> QuickSight, dashboards, or downstream data marts
- Logs and print summaries -> CloudWatch metrics and alarms
- Local environment variables -> Secrets Manager or Parameter Store
- Unit tests -> CI/CD pipeline

## Reference Flow

```text
Local Prototype
  JSONL files + Python + Postgres + PySpark

Production AWS Pattern
  S3 + Kinesis/MSK + Lambda/ECS/Glue + Redshift/Snowflake + EMR/Glue/Databricks + CloudWatch
```

## Scalability Considerations

- Raw JSONL files scale poorly for concurrent producers and consumers, while S3 and Kinesis scale horizontally.
- PostgreSQL is a strong local warehouse, but analytical concurrency and very large fact volumes are better served by Redshift or Snowflake.
- Single-machine Spark is good for local testing; distributed Spark is needed for larger historical windows and more complex joins.
- Streaming consumers should support partitioning, checkpointing, and parallelism when moved to Kinesis/MSK.

## Security Considerations

- Replace hard-coded local defaults with secrets management in production.
- Use IAM roles instead of broad static credentials.
- Encrypt data at rest in S3, Redshift, and Snowflake.
- Encrypt data in transit with TLS between producers, streams, compute, and warehouse layers.
- Apply least-privilege access to raw, processed, and curated data zones.

## Monitoring And Alerting

- Pipeline success/failure counts should become CloudWatch metrics.
- Quarantine counts and unusual activity spikes should trigger alarms.
- Consumer lag and stream throughput should be monitored.
- Warehouse load row counts and rejected rows should be tracked.
- Spark job duration, failed stages, and output row counts should be observed.

## Idempotency

- Warehouse loading already uses idempotent inserts with conflict handling.
- Production batch jobs should use deterministic partitioning and overwrite/merge rules.
- Streaming consumers should use event IDs and deduplication keys to prevent duplicate alerts.
- Replay-safe design matters for retries, consumer restarts, and upstream redelivery.

## Data Quality

- Validation rules should be extended into a formal data quality framework.
- Quarantine zones should preserve bad records for audit and remediation.
- Schema checks, null checks, freshness checks, and distribution anomaly checks should be automated.
- Production systems often add expectations, lineage, and quality SLAs.

## Replay And Backfill Strategy

- Raw data should be retained in immutable storage so downstream layers can be rebuilt.
- Backfills should reprocess from raw or processed zones into curated outputs and warehouse tables.
- Streaming replay should come from retained Kinesis/MSK topics or archived raw events in S3.
- Versioning transformation logic helps explain changes in historical outputs over time.
