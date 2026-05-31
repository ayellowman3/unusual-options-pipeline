# Interview Walkthrough

## 60-Second Version

I built an end-to-end event-driven data pipeline for unusual options activity. The system generates synthetic financial events, validates and quarantines bad records, enriches valid records with unusual-activity signals, produces CSV reports, loads curated data into a warehouse, runs SQL analytics, simulates streaming alerts, and includes a PySpark batch job for distributed-style processing. Locally it uses Python, JSONL, PostgreSQL, pytest, and PySpark, and I documented how it maps to AWS services like S3, Kinesis/MSK, Glue/EMR, Redshift/Snowflake, and CloudWatch.

## 3-Minute Version

The project starts with a synthetic options event generator so I can exercise the pipeline without relying on a live data provider. Those raw events are validated against field-level and business-rule checks, and invalid records are quarantined instead of dropped.

Valid events are enriched with unusual activity features like high volume, volume relative to open interest, and elevated implied volatility. From there, I built multiple downstream consumption paths: CSV reports for quick analysis, a PostgreSQL warehouse with dimensional and fact tables, a SQL analytics runner for business-style queries, a lightweight local streaming simulation that behaves like a producer/consumer alerting system, and a PySpark batch layer that writes Parquet outputs for distributed-style processing.

I used this project to show not just coding ability, but also architectural thinking: batch vs streaming, idempotency, replay, data quality, warehouse modeling, and how a local prototype maps into AWS-native production services.

## Deep-Dive Version

The design intentionally separates concerns by layer:

- generation creates raw domain events
- validation enforces correctness and isolates bad inputs
- enrichment creates analytical signal fields
- reporting provides analyst-friendly outputs
- warehousing normalizes curated entities and facts
- SQL analytics exposes business questions cleanly
- streaming simulation models near-real-time alerting
- Spark batch introduces distributed processing concepts and Parquet outputs

From a data engineering perspective, the important design choices are:
- preserving raw data for replay and backfill
- using quarantine patterns instead of silent drops
- making warehouse loads idempotent
- separating event facts from exploded unusual activity flags
- modeling both low-latency and batch consumption paths
- documenting how the local stack evolves into cloud-native architecture

## How It Maps To The Capital One JD

This project aligns with common Lead Data Engineer expectations:
- building reliable pipelines end to end
- owning data quality and validation strategy
- designing warehouse models and analytical datasets
- working across Python, SQL, and Spark
- balancing batch and streaming patterns
- translating local prototypes into scalable cloud architecture
- communicating tradeoffs and next steps clearly

## How I Would Scale It

- move raw and processed storage to S3
- replace the JSONL stream with Kinesis or MSK
- run enrichment in a managed streaming framework or containerized consumer
- move the warehouse to Redshift or Snowflake
- orchestrate batch flows with Airflow, Step Functions, or managed workflow tooling
- add schema evolution, lineage, and stronger monitoring
- partition Spark outputs by date and symbol for efficient reads

## What I Would Improve Next

- add historical baseline logic for anomaly detection instead of only static thresholds
- add orchestration and scheduling
- add data quality dashboards and SLA monitoring
- add replay tooling for both batch and stream paths
- add API ingestion so the generator can be swapped with a real source
- add warehouse integration tests against a disposable local database

## Behavioral And Ownership Angle

The ownership story here is that I did not stop at a single transformation script. I built a layered system, tested the critical logic, documented tradeoffs, thought through replay and idempotency, and created multiple consumer paths for the same curated data. That demonstrates the mindset of a lead data engineer: not just making code work, but making the system understandable, extensible, and production-minded.
