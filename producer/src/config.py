"""설정을 한 곳에 모은다. 환경변수 > .env > 기본값 순으로 읽는다."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    topic: str = os.getenv("KAFKA_TOPIC", "econ.indicators")
    poll_interval: int = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))

    ecos_api_key: str = os.getenv("ECOS_API_KEY", "")
    kosis_api_key: str = os.getenv("KOSIS_API_KEY", "")


settings = Settings()
