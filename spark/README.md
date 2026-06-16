# spark — Phase 1: Spark Structured Streaming ✅ 동작 검증

Kafka 토픽 `econ.indicators` 를 읽어 event-time 윈도우 집계 후 콘솔/Parquet으로 출력한다.
(Phase 0의 consumer 역할을 대체)

## 실행

### A. Java 없이 Docker로 (이 PC에서 검증된 방법) ⭐

로컬에 JDK가 없어도 Spark 이미지로 바로 돌릴 수 있다. (`docker compose up` 으로 Kafka가 떠 있어야 함)

```bash
docker run --rm --network k8_practice_default \
  -v "$PWD/jobs:/jobs" \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 -e SINK=console -e HOME=/tmp \
  apache/spark:3.5.1 \
  /opt/spark/bin/spark-submit \
    --conf spark.jars.ivy=/tmp/.ivy2 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
    /jobs/streaming_aggregation.py
```

> `spark.jars.ivy=/tmp/.ivy2` 가 핵심 — 컨테이너의 기본 ivy 캐시(`/home/spark/.ivy2`)가
> 쓰기 불가라 connector 다운로드가 실패한다. 쓰기 가능한 `/tmp` 로 돌려준다.
> (Windows Git Bash라면 경로 변환 방지로 앞에 `MSYS_NO_PATHCONV=1` 를 붙이고 `-v "D:/.../jobs:/jobs"` 형태로.)

### B. 로컬 JDK가 있다면

```bash
pip install -r requirements.txt
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 jobs/streaming_aggregation.py
```

## 환경변수

| 변수 | 기본 | 설명 |
|------|------|------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:29092` | 호스트=29092, 컨테이너망=`kafka:9092`, K8s=`econ-kafka-kafka-bootstrap:9092` |
| `KAFKA_TOPIC` | `econ.indicators` | 구독 토픽 |
| `SINK` | `console` | `console`(검증용) 또는 `parquet`(적재) |
| `OUTPUT_PATH` / `CHECKPOINT_PATH` | `/tmp/econ/...` | parquet sink 경로 |

## 검증된 출력 예시

```
Batch: 3
|start              |end                |indicator|avg_value|max_value|cnt|
|2026-06-16 08:02:00|2026-06-16 08:03:00|kospi    |2309.31  |2362.03  |30 |
|2026-06-16 08:02:00|2026-06-16 08:03:00|base_rate|3.144    |3.1989   |30 |
```

윈도우(1분, 30초 슬라이드)별 지표 평균/최대/건수가 마이크로배치마다 갱신된다.

## 다음 단계 (Phase 2)

`spark/Dockerfile` 로 `econ-spark:0.1` 이미지를 빌드해 `k8s/spark/spark-application.yaml`(Spark Operator)로 제출한다.
