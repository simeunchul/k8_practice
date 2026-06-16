"""Kafka producer 진입점.

  python -m src.producer --mock   # 가짜 이벤트 (API 키 불필요)
  python -m src.producer          # 실제 ECOS 수집 (TODO 완성 후)
"""
import argparse
import json
import random
import time

from confluent_kafka import Producer

from .config import settings
from .ecos_client import EcosClient

# mock 모드에서 사용할 가짜 지표 카탈로그
MOCK_INDICATORS = [
    ("base_rate", "기준금리", 3.5),
    ("usd_krw", "원달러환율", 1350.0),
    ("kospi", "코스피", 2600.0),
    ("cpi", "소비자물가지수", 114.0),
]


def _delivery_report(err, msg):
    if err is not None:
        print(f"  ✗ 발행 실패: {err}")
    else:
        print(f"  ✓ {msg.topic()}[{msg.partition()}] @ offset {msg.offset()}")


def make_producer() -> Producer:
    return Producer({"bootstrap.servers": settings.bootstrap_servers})


def run_mock(producer: Producer):
    """무작위 워크로 지표 값을 흔들며 계속 발행한다."""
    state = {code: base for code, _, base in MOCK_INDICATORS}
    print(f"[mock] '{settings.topic}' 토픽으로 {settings.poll_interval}s 간격 발행 시작")
    while True:
        for code, name, _ in MOCK_INDICATORS:
            state[code] *= 1 + random.uniform(-0.01, 0.01)
            event = {
                "indicator": code,
                "name": name,
                "value": round(state[code], 4),
                "ts": int(time.time() * 1000),
                "source": "mock",
            }
            producer.produce(
                settings.topic,
                key=code,
                value=json.dumps(event, ensure_ascii=False),
                callback=_delivery_report,
            )
        producer.poll(0)
        time.sleep(settings.poll_interval)


def run_ecos(producer: Producer):
    """실제 ECOS 수집. TODO: ecos_client.fetch_statistic 결과를 이벤트로 변환해 발행."""
    if not settings.ecos_api_key:
        raise SystemExit("ECOS_API_KEY 가 없습니다. .env 설정 후 다시 실행하거나 --mock 을 쓰세요.")
    client = EcosClient(settings.ecos_api_key)  # noqa: F841  (TODO에서 사용)
    raise NotImplementedError("ECOS 수집은 Phase 0 후반 TODO입니다. ecos_client.py 참고.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="가짜 이벤트 발행 (API 키 불필요)")
    args = parser.parse_args()

    producer = make_producer()
    try:
        if args.mock:
            run_mock(producer)
        else:
            run_ecos(producer)
    except KeyboardInterrupt:
        print("\n종료 중... 버퍼 flush")
    finally:
        producer.flush(10)


if __name__ == "__main__":
    main()
