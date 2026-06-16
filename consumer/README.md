# consumer — 오프셋 학습용 단순 Consumer

Phase 0에서 Kafka의 핵심 개념(컨슈머 그룹, 파티션, 오프셋 커밋)을 손에 익히기 위한 최소 consumer.
Phase 1에서 이 역할은 Spark Structured Streaming으로 대체된다.

## 실행

```bash
pip install -r requirements.txt
python -m src.consumer
```

## 관찰 포인트

- 같은 `group.id` 로 consumer를 2개 띄우면 파티션이 어떻게 나뉘는가 (리밸런싱)
- `enable.auto.commit=False` 로 두고 수동 커밋 → kafka-ui에서 컨슈머 그룹의 lag 변화
- consumer를 껐다 켜면 마지막 커밋 오프셋부터 이어 읽는지
