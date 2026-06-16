# spark — Phase 1: Spark Structured Streaming

Kafka 토픽을 읽어 윈도우 집계 후 Parquet으로 적재한다. (Phase 0의 consumer 역할을 대체)

## 로컬 실행 (패키지 자동 다운로드)

```bash
pip install -r requirements.txt

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  jobs/streaming_aggregation.py
```

> `--packages` 가 처음 한 번은 의존 jar를 받아오므로 인터넷 필요. 로컬 모드(`local[*]`)면 클러스터 불필요.

## Phase 1 체크리스트

- [ ] Kafka source 에서 JSON 파싱 (schema 정의)
- [ ] event-time 기준 슬라이딩 윈도우 집계 (예: 1분 윈도우 평균/최대)
- [ ] watermark로 지연 이벤트 처리
- [ ] Parquet sink + checkpoint (정확히 한 번 보장 관찰)
- [ ] (선택) Postgres에 집계 결과 upsert

## 다음 단계

Phase 2에서 이 잡을 컨테이너 이미지로 만들어 `k8s/spark/` 의 SparkApplication CRD로 제출한다.
