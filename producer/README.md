# producer — 경제지표 Kafka Producer

ECOS/KOSIS OpenAPI를 주기적으로 폴링해 경제지표 이벤트를 Kafka 토픽으로 발행한다.
API 키가 없어도 `--mock` 모드로 가짜 이벤트를 생성해 Phase 0를 바로 돌려볼 수 있다.

## 실행

```bash
pip install -r requirements.txt

# 가짜 이벤트 (API 키 불필요) — Phase 0 학습용
python -m src.producer --mock

# 실제 ECOS 수집 (.env 에 ECOS_API_KEY 필요)
python -m src.producer
```

## 파일

- `src/config.py`      — `.env` 로딩, 설정 한 곳에 모음
- `src/ecos_client.py` — ECOS OpenAPI 클라이언트 (**TODO: 실제 엔드포인트 구현**)
- `src/producer.py`    — Kafka 발행 루프 (mock / 실수집 진입점)

## Phase 0 체크리스트

- [ ] `docker compose up -d` 로 브로커 확인
- [ ] `--mock` 으로 토픽에 메시지 발행, kafka-ui에서 확인
- [ ] consumer로 소비하며 오프셋이 증가하는지 관찰
- [ ] `ecos_client.py` 의 TODO를 채워 실제 ECOS 지표 수집으로 교체
