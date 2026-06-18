#!/usr/bin/env bash
# Phase 2 (경량) — kind 로컬 K8s 클러스터에 econ 파이프라인 1건을 실제로 배포·운영.
# Strimzi/Spark/Helm 없이 단일노드 Kafka + producer + consumer 만으로 K8s 배포·운영을 검증한다.
#
# 사전: Docker Desktop 실행 중 + kind + kubectl
# 실행: bash k8s/local/run-local-kind.sh
set -euo pipefail

CLUSTER=econ
NS=econ
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"

echo "▶ 1. kind 클러스터 생성 (이미 있으면 건너뜀)"
if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  kind create cluster --name "$CLUSTER" --config "$HERE/kind-cluster.yaml"
fi
kubectl cluster-info --context "kind-$CLUSTER"

echo "▶ 2. producer / consumer 이미지 빌드"
docker build -t econ-producer:0.1 "$ROOT/producer"
docker build -t econ-consumer:0.1 "$ROOT/consumer"

echo "▶ 3. 이미지를 kind 노드로 로드 (레지스트리 불필요)"
kind load docker-image econ-producer:0.1 --name "$CLUSTER"
kind load docker-image econ-consumer:0.1 --name "$CLUSTER"

echo "▶ 4. 매니페스트 적용"
kubectl apply -f "$ROOT/k8s/namespace.yaml"
kubectl apply -f "$HERE/kafka.yaml"
echo "   Kafka Ready 대기 (최대 4분)..."
kubectl -n "$NS" rollout status deploy/kafka --timeout=240s
kubectl apply -f "$HERE/producer.yaml"
kubectl apply -f "$HERE/consumer.yaml"
kubectl -n "$NS" rollout status deploy/econ-producer --timeout=120s
kubectl -n "$NS" rollout status deploy/econ-consumer --timeout=120s

echo "▶ 5. 배포 상태"
kubectl get pods,svc,deploy -n "$NS" -o wide

cat <<EOF

✅ 배포 완료. 운영(operate) 확인 명령:
   kubectl logs -n $NS -l app=econ-producer -f      # 발행 로그
   kubectl logs -n $NS -l app=econ-consumer -f      # 소비 + 오프셋 커밋
   kubectl -n $NS scale deploy/econ-consumer --replicas=2     # 스케일
   kubectl -n $NS rollout restart deploy/econ-producer        # 롤아웃
   kubectl -n $NS rollout status  deploy/econ-producer

정리: kind delete cluster --name $CLUSTER
EOF
