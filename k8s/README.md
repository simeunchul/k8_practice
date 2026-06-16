# k8s — Phase 2: 파이프라인을 Kubernetes 위로

로컬 클러스터(minikube 또는 kind)에 Strimzi(Kafka), Spark Operator, producer를 올린다.
**여기가 면접 레버리지가 가장 큰 단계.**

## 준비

```bash
# 클러스터 (둘 중 하나)
minikube start --cpus 4 --memory 8192
# 또는: kind create cluster --name econ

kubectl create namespace econ
```

## 1. Kafka — Strimzi 오퍼레이터

```bash
kubectl create -f 'https://strimzi.io/install/latest?namespace=econ' -n econ
kubectl apply -f kafka/kafka-cluster.yaml -n econ      # TODO: Kafka CR 작성
```

## 2. Spark — Spark Operator

```bash
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm install spark-operator spark-operator/spark-operator -n econ
kubectl apply -f spark/spark-application.yaml -n econ  # TODO: SparkApplication CR
```

## 3. Producer — CronJob / Deployment

```bash
# 이미지 빌드 후 클러스터로 로드
docker build -t econ-producer:0.1 ../producer
minikube image load econ-producer:0.1                 # kind: kind load docker-image
kubectl apply -f producer/cronjob.yaml -n econ        # TODO: CronJob 작성
```

## 폴더 (작성 예정)

```
k8s/
├── namespace.yaml
├── kafka/kafka-cluster.yaml        # Strimzi Kafka CR
├── spark/spark-application.yaml    # SparkApplication CR
└── producer/cronjob.yaml           # producer CronJob
```

## Phase 2 체크리스트

- [ ] minikube/kind 클러스터 기동, `kubectl get nodes`
- [ ] Strimzi로 Kafka 클러스터 1개 띄우고 토픽 CR 생성
- [ ] producer 이미지 빌드 → 클러스터 로드 → CronJob 발행 확인
- [ ] Spark Operator로 streaming 잡 제출, `kubectl logs` 로 집계 관찰
- [ ] `kubectl port-forward` 로 kafka-ui 또는 Spark UI 접근
