from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql import types as T

from omnichannel_platform.common.logging import get_logger

LOGGER = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spark starter job for Retailrocket sessionization."
    )
    parser.add_argument("--input-path", default="data/sample/streaming/retailrocket_events.jsonl")
    parser.add_argument("--output-path", default="storage/gold/retailrocket_sessions")
    parser.add_argument("--gap-minutes", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Retailrocket replay input not found: {input_path}")

    spark = SparkSession.builder.appName("clickstream-sessionization-starter").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    schema = T.StructType(
        [
            T.StructField("event_id", T.StringType(), True),
            T.StructField("visitor_id", T.StringType(), True),
            T.StructField("event_type", T.StringType(), True),
            T.StructField("item_id", T.StringType(), True),
            T.StructField("transaction_id", T.StringType(), True),
            T.StructField("event_ts", T.StringType(), True),
        ]
    )

    raw_events = spark.read.schema(schema).json(str(input_path))
    normalized_events = (
        raw_events.withColumn("event_type", F.lower(F.col("event_type")))
        .withColumn("event_ts", F.to_timestamp("event_ts"))
        .filter(F.col("event_id").isNotNull() & F.col("visitor_id").isNotNull())
    )

    window = Window.partitionBy("visitor_id").orderBy("event_ts", "event_id")
    sessionized = (
        normalized_events.withColumn("previous_event_ts", F.lag("event_ts").over(window))
        .withColumn(
            "is_new_session",
            F.when(F.col("previous_event_ts").isNull(), F.lit(1))
            .when(
                F.unix_timestamp("event_ts") - F.unix_timestamp("previous_event_ts")
                > args.gap_minutes * 60,
                F.lit(1),
            )
            .otherwise(F.lit(0)),
        )
        .withColumn(
            "session_number",
            F.sum("is_new_session").over(window.rowsBetween(Window.unboundedPreceding, 0)),
        )
        .withColumn(
            "session_key",
            F.concat_ws("-", F.col("visitor_id"), F.col("session_number").cast("string")),
        )
    )

    session_summary = sessionized.groupBy("session_key", "visitor_id").agg(
        F.min("event_ts").alias("session_start_ts"),
        F.max("event_ts").alias("session_end_ts"),
        F.count("*").alias("event_count"),
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("view_count"),
        F.sum(F.when(F.col("event_type") == "addtocart", 1).otherwise(0)).alias("addtocart_count"),
        F.sum(F.when(F.col("event_type") == "transaction", 1).otherwise(0)).alias(
            "transaction_count"
        ),
        F.min("item_id").alias("sample_item_id"),
    )

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    session_summary.write.mode("overwrite").parquet(str(output_path))

    LOGGER.info(
        "Spark sessionization wrote %s session rows to %s",
        session_summary.count(),
        output_path,
    )
    spark.stop()


if __name__ == "__main__":
    main()
