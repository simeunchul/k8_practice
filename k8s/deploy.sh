#!/usr/bin/env bash
# Phase 2 — 로컬 클러스터(minikube/kind)에 전체 파이프라인 배포.
# 사전: minikube start (또는 kind create cluster), helm 설치.
set -euo pipefail
NS=econ

echo "▶ 0. 네임스페이스"
kubectl apply -f namespace.yaml

echo "▶ 1. Strimzi 오퍼레이터 설치"
kubectl create -f "https://strimzi.io/install/latest?namespace=${NS}" -n "${NS}" || true
kubectl -n "${NS}" wait deploy/strimzi-cluster-operator --for=condition=Available --timeout=300s

echo "▶ 2. Kafka 클러스터 + 토픽"
kubectl apply -f kafka/kafka-cluster.yaml -n "${NS}"
kubectl -n "${NS}" wait kafka/econ-kafka --for=condition=Ready --timeout=600s
kubectl apply -f kafka/topic.yaml -n "${NS}"

echo "▶ 3. producer 이미지 빌드 & 로드"
docker build -t econ-producer:0.1 ../producer
# minikube: minikube image load econ-producer:0.1
# kind:     kind load docker-image econ-producer:0.1
echo "  (위 주석 중 사용하는 클러스터에 맞는 image load 명령을 실행하세요)"
kubectl apply -f producer/deployment.yaml -n "${NS}"

echo "▶ 4. Spark Operator + 스트리밍 잡"
helm repo add spark-operator https://kubeflow.github.io/spark-operator || true
helm repo update
helm upgrade --install spark-operator spark-operator/spark-operator \
  -n "${NS}" --set "spark.jobNamespaces={${NS}}"
docker build -t econ-spark:0.1 ../spark
# minikube image load econ-spark:0.1  /  kind load docker-image econ-spark:0.1
kubectl apply -f spark/rbac.yaml -n "${NS}"
kubectl apply -f spark/spark-application.yaml -n "${NS}"

echo "✅ 배포 완료. 상태 확인:"
echo "   kubectl get pods -n ${NS} -w"
echo "   kubectl logs -n ${NS} -l app=econ-producer -f"
echo "   kubectl logs -n ${NS} econ-streaming-agg-driver -f"
