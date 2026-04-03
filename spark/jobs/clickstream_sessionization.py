from __future__ import annotations

import argparse

from pyspark.sql import SparkSession


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter Spark job for clickstream sessionization.")
    parser.add_argument("--input-path", default="TODO_INPUT_PATH")
    parser.add_argument("--output-path", default="TODO_OUTPUT_PATH")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("clickstream-sessionization-starter").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    print(f"Spark starter job initialized for input={args.input_path} output={args.output_path}")
    print("TODO: implement schema loading, sessionization logic, and output writes.")

    spark.stop()


if __name__ == "__main__":
    main()

