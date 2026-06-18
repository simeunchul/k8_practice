# Phase 2 — K8s Deployment 이미지 (consumer)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# K8s에서는 KAFKA_BOOTSTRAP_SERVERS 를 클러스터 내부 주소(kafka:9092)로 주입
ENTRYPOINT ["python", "-m", "src.consumer"]
