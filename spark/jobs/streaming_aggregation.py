"""Phase 1 — Kafka → Spark Structured Streaming → (console | parquet).

Kafka 토픽 econ.indicators 를 읽어 event-time 윈도우로 집계한다.

환경변수
  KAFKA_BOOTSTRAP_SERVERS  브로커 주소 (로컬 docker: localhost:29092 / 컨테이너망: kafka:9092)
  KAFKA_TOPIC              구독 토픽 (기본 econ.indicators)
  SINK                     출력 sink: console(기본) | parquet
  OUTPUT_PATH              parquet sink 경로 (기본 /tmp/econ/agg)
  CHECKPOINT_PATH          checkpoint 경로 (기본 /tmp/econ/checkpoint)

로컬 실행 (Java 설치 시):
  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 jobs/streaming_aggregation.py

로컬 실행 (Java 없이 Docker로):
  docker run --rm --network k8_practice_default -v "$PWD/spark/jobs:/jobs" \\
    -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 apache/spark:3.5.1 \\
    /opt/spark/bin/spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \\
    /jobs/streaming_aggregation.py
"""
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructType

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
TOPIC = os.getenv("KAFKA_TOPIC", "econ.indicators")
SINK = os.getenv("SINK", "console").lower()
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "/tmp/econ/agg")
CHECKPOINT = os.getenv("CHECKPOINT_PATH", "/tmp/econ/checkpoint")
KAFKA_PACKAGE = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"

# producer가 발행하는 이벤트 스키마
EVENT_SCHEMA = (
    StructType()
    .add("indicator", StringType())
    .add("name", StringType())
    .add("value", DoubleType())
    .add("ts", LongType())
    .add("source", StringType())
)


def build_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("econ-streaming-agg")
        # spark-submit --packages 없이 python으로 직접 실행할 때도 connector를 받아오도록
        .config("spark.jars.packages", KAFKA_PACKAGE)
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    # value(bytes) → JSON 파싱 → event_time 컬럼 생성
    parsed = (
        raw.select(F.from_json(F.col("value").cast("string"), EVENT_SCHEMA).alias("e"))
        .select("e.*")
        .withColumn("event_time", (F.col("ts") / 1000).cast("timestamp"))
    )

    # event-time 1분 윈도우(30초 슬라이드) + 워터마크로 지각 이벤트 정리
    agg = (
        parsed.withWatermark("event_time", "2 minutes")
        .groupBy(F.window("event_time", "1 minute", "30 seconds"), F.col("indicator"))
        .agg(
            F.round(F.avg("value"), 4).alias("avg_value"),
            F.round(F.max("value"), 4).alias("max_value"),
            F.count("*").alias("cnt"),
        )
        .select("window.start", "window.end", "indicator", "avg_value", "max_value", "cnt")
    )

    if SINK == "parquet":
        query = (
            agg.writeStream.outputMode("append")  # 윈도우가 워터마크를 지나면 확정 출력
            .format("parquet")
            .option("path", OUTPUT_PATH)
            .option("checkpointLocation", CHECKPOINT)
            .partitionBy("indicator")
            .trigger(processingTime="30 seconds")
            .start()
        )
    else:
        query = (
            agg.writeStream.outputMode("update")
            .format("console")
            .option("truncate", "false")
            .trigger(processingTime="10 seconds")
            .start()
        )

    query.awaitTermination()


if __name__ == "__main__":
    main()
