# Tradeoffs

## Batch vs Streaming

Batch is simpler, cheaper to reason about, and strong for historical analytics. Streaming is better for alerting and low-latency responses but introduces operational complexity, ordering concerns, checkpointing, and replay design.

## Postgres vs Redshift/Snowflake

Postgres is ideal for local development, small-scale warehousing, and schema iteration. Redshift and Snowflake are stronger for large-scale analytical workloads, concurrency, elastic compute, and BI integration.

## JSONL vs Parquet

JSONL is easy to inspect, append, and use for event simulation. Parquet is much better for analytical scan performance, compression, schema-aware reads, and distributed processing.

## Local JSONL Stream vs Kafka/Kinesis

The local JSONL stream is lightweight and interview-friendly, but it lacks partitioning, offsets, durability guarantees, scaling behavior, consumer groups, and native observability. Kafka/Kinesis provide those production-grade streaming capabilities.

## Python Processing vs Spark Processing

Pure Python processing is fast to build, easy to test, and great for small datasets. Spark becomes valuable when data volume, partitioned processing, wide aggregations, and distributed compute matter more than local simplicity.

## Fake Data vs Real API Data

Synthetic data is reliable, controllable, and ideal for practicing pipeline design. Real API data introduces authentication, rate limits, schema drift, market hours, backfill constraints, vendor SLAs, and richer production realism.

## Simple Rule-Based Unusual Activity vs Historical/Statistical Baseline

Rule-based scoring is interpretable and easy to explain in interviews. A real production detector would likely use historical distributions, z-scores, volatility context, peer comparisons, or model-based anomaly detection for better signal quality.

## Local Project vs Production Deployment

This local project optimizes for clarity and breadth. A production deployment would add orchestration, observability, security controls, CI/CD, infrastructure as code, schema evolution strategy, lineage, and cost management.
