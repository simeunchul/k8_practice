"""오프셋을 수동 커밋하며 메시지를 소비하는 학습용 consumer."""
import json
import os

from confluent_kafka import Consumer
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
TOPIC = os.getenv("KAFKA_TOPIC", "econ.indicators")
GROUP = os.getenv("KAFKA_GROUP_ID", "econ-consumer-1")


def main():
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "group.id": GROUP,
            "auto.offset.reset": "earliest",  # 그룹 첫 실행 시 토픽 처음부터
            "enable.auto.commit": False,       # 오프셋 직접 커밋해보기
        }
    )
    consumer.subscribe([TOPIC])
    print(f"'{TOPIC}' 구독 시작 (group={GROUP}). Ctrl+C로 종료.")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"  ✗ {msg.error()}")
                continue

            event = json.loads(msg.value())
            print(
                f"  [{msg.partition()}@{msg.offset()}] "
                f"{event['name']}={event['value']}"
            )
            consumer.commit(msg)  # 처리 성공 후 수동 커밋
    except KeyboardInterrupt:
        print("\n종료")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
