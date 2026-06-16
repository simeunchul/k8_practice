# k8s — Phase 2: 파이프라인을 Kubernetes 위로

로컬 클러스터(minikube/kind)에 Strimzi(Kafka), Spark Operator, producer를 올린다.
**면접 레버리지가 가장 큰 단계.** 모든 manifest는 작성 완료, 클러스터만 있으면 `deploy.sh` 로 한 번에 배포된다.

## 파일

```
k8s/
├── namespace.yaml                  # econ 네임스페이스
├── deploy.sh                       # 전체 배포 오케스트레이션 스크립트
├── kafka/
│   ├── kafka-cluster.yaml          # Strimzi Kafka(KRaft) + KafkaNodePool
│   └── topic.yaml                  # KafkaTopic econ.indicators (파티션 3)
├── producer/
│   ├── deployment.yaml             # producer 상시 실행
│   └── secret.example.yaml         # 실수집 시 ECOS 키 Secret
└── spark/
    ├── rbac.yaml                   # SparkApplication driver용 ServiceAccount/Role
    └── spark-application.yaml      # Spark Operator SparkApplication CR
```

## 사전 준비

```bash
minikube start --cpus 4 --memory 8192      # 또는: kind create cluster --name econ
# helm 설치 필요
```

## 한 번에 배포

```bash
cd k8s
bash deploy.sh
```

`deploy.sh` 가 하는 일: 네임스페이스 → Strimzi 오퍼레이터 → Kafka+토픽 → producer 이미지 빌드/배포 → Spark Operator(helm) → SparkApplication 제출.

> ⚠️ 이미지 로드: minikube는 `minikube image load econ-producer:0.1`, kind는 `kind load docker-image econ-producer:0.1`.
> deploy.sh 안에 주석으로 표시해 뒀으니 사용하는 클러스터에 맞게 실행.

## 단계별 수동 배포 (학습용)

```bash
kubectl apply -f namespace.yaml
kubectl create -f 'https://strimzi.io/install/latest?namespace=econ' -n econ
kubectl apply -f kafka/kafka-cluster.yaml -n econ
kubectl wait kafka/econ-kafka --for=condition=Ready --timeout=600s -n econ
kubectl apply -f kafka/topic.yaml -n econ

docker build -t econ-producer:0.1 ../producer && minikube image load econ-producer:0.1
kubectl apply -f producer/deployment.yaml -n econ

helm repo add spark-operator https://kubeflow.github.io/spark-operator && helm repo update
helm install spark-operator spark-operator/spark-operator -n econ --set "spark.jobNamespaces={econ}"
docker build -t econ-spark:0.1 ../spark && minikube image load econ-spark:0.1
kubectl apply -f spark/rbac.yaml -n econ
kubectl apply -f spark/spark-application.yaml -n econ
```

## 관찰 포인트 (Phase 2 체크리스트)

- [ ] `kubectl get pods -n econ -w` — Kafka, producer, spark driver/executor 파드가 뜨는지
- [ ] `kubectl logs -n econ -l app=econ-producer -f` — 발행 로그
- [ ] `kubectl logs -n econ econ-streaming-agg-driver -f` — 집계 배치 출력
- [ ] `kubectl get kafkatopic -n econ` — 토픽이 3 파티션으로 생성됐는지
- [ ] producer를 `replicas: 2` 로 늘리거나 executor를 늘려 파티션 분산 관찰

## 정리

```bash
kubectl delete namespace econ
minikube delete   # 또는 kind delete cluster --name econ
```
