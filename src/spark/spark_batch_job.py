from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_spark_session(app_name: str = "UnusualOptionsSparkBatch"):
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.master("local[*]")
        .appName(app_name)
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def read_enriched_events(spark, input_path: str):
    return spark.read.json(input_path)


def transform_events(df):
    from pyspark.sql import functions as F

    return (
        df.withColumn("event_timestamp", F.to_timestamp("event_timestamp"))
        .withColumn("expiration_date", F.to_date("expiration_date"))
        .withColumn("event_date", F.to_date("event_timestamp"))
        .withColumn("event_hour", F.hour("event_timestamp"))
        .withColumn("volume", F.col("volume").cast("int"))
        .withColumn("open_interest", F.col("open_interest").cast("int"))
        .withColumn("implied_volatility", F.col("implied_volatility").cast("double"))
        .withColumn("unusual_activity_score", F.col("unusual_activity_score").cast("int"))
        .withColumn("volume_open_interest_ratio", F.col("volume_open_interest_ratio").cast("double"))
        .withColumn("underlying_price", F.col("underlying_price").cast("double"))
        .withColumn("strike", F.col("strike").cast("double"))
    )


def get_unusual_events(df):
    from pyspark.sql import functions as F

    return df.filter(F.col("unusual_activity_score") > 0)


def get_symbol_daily_summary(df):
    from pyspark.sql import functions as F

    return (
        df.groupBy("symbol", "event_date")
        .agg(
            F.count("*").alias("total_events"),
            F.sum(F.when(F.col("unusual_activity_score") > 0, 1).otherwise(0)).alias("unusual_events"),
            F.sum("volume").alias("total_volume"),
            F.round(F.avg("implied_volatility"), 4).alias("avg_implied_volatility"),
            F.round(F.avg("unusual_activity_score"), 4).alias("avg_unusual_activity_score"),
        )
        .withColumn(
            "unusual_event_pct",
            F.round(F.col("unusual_events") / F.col("total_events"), 4),
        )
        .select(
            "symbol",
            "event_date",
            "total_events",
            "unusual_events",
            "unusual_event_pct",
            "total_volume",
            "avg_implied_volatility",
            "avg_unusual_activity_score",
        )
    )


def get_flag_summary(df):
    from pyspark.sql import functions as F

    return (
        df.withColumn("flag", F.explode_outer("unusual_activity_flags"))
        .filter(F.col("flag").isNotNull())
        .groupBy("flag")
        .agg(F.count("*").alias("flag_count"))
        .orderBy(F.col("flag_count").desc(), F.col("flag").asc())
    )


def get_option_type_summary(df):
    from pyspark.sql import functions as F

    return (
        df.groupBy("option_type")
        .agg(
            F.count("*").alias("total_events"),
            F.sum(F.when(F.col("unusual_activity_score") > 0, 1).otherwise(0)).alias("unusual_events"),
            F.sum("volume").alias("total_volume"),
            F.round(F.avg("implied_volatility"), 4).alias("avg_implied_volatility"),
            F.round(F.avg("unusual_activity_score"), 4).alias("avg_unusual_activity_score"),
        )
        .withColumn(
            "unusual_event_pct",
            F.round(F.col("unusual_events") / F.col("total_events"), 4),
        )
        .select(
            "option_type",
            "total_events",
            "unusual_events",
            "unusual_event_pct",
            "total_volume",
            "avg_implied_volatility",
            "avg_unusual_activity_score",
        )
        .orderBy("option_type")
    )


def write_output(df, output_path: str, mode: str = "overwrite") -> None:
    df.write.mode(mode).parquet(output_path)


def run_spark_batch(input_path: str, output_dir: str) -> None:
    spark = create_spark_session()

    try:
        transformed_df = transform_events(read_enriched_events(spark, input_path))
        unusual_events_df = get_unusual_events(transformed_df)
        symbol_daily_summary_df = get_symbol_daily_summary(transformed_df)
        flag_summary_df = get_flag_summary(transformed_df)
        option_type_summary_df = get_option_type_summary(transformed_df)

        write_output(unusual_events_df, f"{output_dir}/unusual_events")
        write_output(symbol_daily_summary_df, f"{output_dir}/symbol_daily_summary")
        write_output(flag_summary_df, f"{output_dir}/flag_summary")
        write_output(option_type_summary_df, f"{output_dir}/option_type_summary")

        print(f"Wrote unusual events to {output_dir}/unusual_events")
        print(f"Wrote symbol daily summary to {output_dir}/symbol_daily_summary")
        print(f"Wrote flag summary to {output_dir}/flag_summary")
        print(f"Wrote option type summary to {output_dir}/option_type_summary")
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local PySpark batch job over enriched options events.")
    parser.add_argument("--input", default="data/processed/options_events_enriched.jsonl")
    parser.add_argument("--output-dir", default="data/spark_output")
    args = parser.parse_args()

    run_spark_batch(input_path=args.input, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
