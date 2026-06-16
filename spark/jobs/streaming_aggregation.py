"""Phase 1 — Kafka → Spark Structured Streaming → Parquet.

골격만 잡아둠. TODO를 채우며 Spark의 윈도우/워터마크/checkpoint를 익힌다.
로컬 실행:
  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 jobs/streaming_aggregation.py
"""
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructType, DoubleType

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
TOPIC = os.getenv("KAFKA_TOPIC", "econ.indicators")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output/agg")
CHECKPOINT = os.getenv("CHECKPOINT_PATH", "checkpoint/agg")

# producer가 발행하는 이벤트 스키마
EVENT_SCHEMA = (
    StructType()
    .add("indicator", StringType())
    .add("name", StringType())
    .add("value", DoubleType())
    .add("ts", LongType())
    .add("source", StringType())
)


def main():
    spark = (
        SparkSession.builder.appName("econ-streaming-agg")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    parsed = (
        raw.select(F.from_json(F.col("value").cast("string"), EVENT_SCHEMA).alias("e"))
        .select("e.*")
        .withColumn("event_time", (F.col("ts") / 1000).cast("timestamp"))
    )

    # TODO: event-time 1분 슬라이딩 윈도우 + watermark 집계
    agg = (
        parsed.withWatermark("event_time", "2 minutes")
        .groupBy(F.window("event_time", "1 minute", "30 seconds"), F.col("indicator"))
        .agg(
            F.avg("value").alias("avg_value"),
            F.max("value").alias("max_value"),
            F.count("*").alias("cnt"),
        )
    )

    # 우선 콘솔로 확인 → 익숙해지면 아래 Parquet sink로 교체
    query = (
        agg.writeStream.outputMode("update")
        .format("console")
        .option("truncate", "false")
        .start()
    )

    # Parquet sink 예시 (append + checkpoint):
    # query = (
    #     agg.writeStream.outputMode("append")
    #     .format("parquet")
    #     .option("path", OUTPUT_PATH)
    #     .option("checkpointLocation", CHECKPOINT)
    #     .partitionBy("indicator")
    #     .start()
    # )

    query.awaitTermination()


if __name__ == "__main__":
    main()
