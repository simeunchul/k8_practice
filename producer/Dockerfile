# Phase 2에서 K8s CronJob 이미지로 사용
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# K8s에서는 KAFKA_BOOTSTRAP_SERVERS 를 클러스터 내부 주소로 주입
ENTRYPOINT ["python", "-m", "src.producer"]
