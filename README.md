# econ-stream — 경제지표 실시간 수집·집계 파이프라인

`ECOS / KOSIS / 열린재정` OpenAPI에서 경제지표를 수집해 **Kafka → Spark → S3**로 흘려보내고,
전체를 **Kubernetes** 위에서 **Airflow**로 오케스트레이션하는 토이 파이프라인.

> **목적**: K8s · Kafka · Spark · AWS 4종을 *하나의 데이터 엔지니어링 파이프라인*으로 관통해 본다.
> 데이터 소스는 새로 배우지 않도록 이미 익숙한 경제지표 OpenAPI를 그대로 쓴다.

---

## 아키텍처

```
ECOS/KOSIS poller          Kafka              Spark Structured        S3 (Parquet)
(producer, Python)   →    topic        →      Streaming         →     날짜 파티션
 주기적 API 호출          (Strimzi)           윈도우 집계              + Postgres(집계결과)

└──────────────── 전부 K8s 위에서 (local: minikube/kind → AWS: EKS) ──────────────┘
                  오케스트레이션: Airflow + KubernetesExecutor
```

자세한 데이터 흐름은 [docs/architecture.md](docs/architecture.md) 참고.

---

## 단계별 로드맵

각 단계는 **"이미 손댐" 증거물 1개**를 남기는 걸 목표로 한다. 앞 단계만 끝내도 가치가 나오도록 순서를 짰다.

| 단계 | 내용 | 폴더 | 새 기술 | 상태 |
|------|------|------|---------|------|
| **Phase 0** | docker-compose로 Kafka 띄우고 `producer → topic → consumer → 오프셋 커밋` | [producer/](producer/), [consumer/](consumer/) | Kafka | ✅ 동작 검증 |
| **Phase 1** | consumer를 PySpark Structured Streaming으로 교체, 윈도우 집계 → Parquet | [spark/](spark/) | Spark | ⬜ |
| **Phase 2** | minikube/kind 위로: Strimzi(Kafka) + Spark Operator + producer CronJob | [k8s/](k8s/) | **K8s** | ⬜ |
| **Phase 3** | Airflow + KubernetesExecutor로 수집/백필 DAG 오케스트레이션 | [airflow/](airflow/) | K8s·Airflow | ⬜ |
| **Phase 4** | eksctl/Terraform으로 EKS 승격, S3 적재. 하루 켜고 스크린샷 후 destroy | [aws/](aws/) | AWS | ⬜ |

> 시간이 빠듯하면 Phase 0~2(Kafka + Spark + K8s)까지만 해도 "4종 중 3종 손댐 + AWS는 설계까지"가 된다.
> Phase 4는 최악의 경우 README의 아키텍처 + IaC 코드만 있어도 어필 가능.

---

## 빠른 시작 (Phase 0)

```bash
# 1. 환경 변수 준비 (ECOS 키 없어도 mock 모드로 동작)
cp .env.example .env

# 2. Kafka + kafka-ui 띄우기
docker compose up -d

# 3. producer: 가짜 경제지표 이벤트를 토픽에 발행 (mock 모드)
cd producer && pip install -r requirements.txt && python -m src.producer --mock

# 4. consumer: 메시지 소비 + 오프셋 커밋 확인 (다른 터미널)
cd consumer && pip install -r requirements.txt && python -m src.consumer

# 5. 브라우저에서 토픽/파티션/오프셋 눈으로 확인
#    kafka-ui → http://localhost:8080
```

---

## 폴더 구조

```
k8_practice/
├── README.md               # 이 파일 (전체 로드맵)
├── docker-compose.yml      # Phase 0: 로컬 Kafka(KRaft) + kafka-ui
├── .env.example            # API 키, 브로커 주소 등
├── producer/               # Phase 0: ECOS/KOSIS poller → Kafka producer
├── consumer/               # Phase 0: 오프셋 학습용 단순 consumer
├── spark/                  # Phase 1: Spark Structured Streaming 잡
├── k8s/                    # Phase 2: Strimzi / Spark Operator manifest
├── airflow/                # Phase 3: KubernetesExecutor DAG + helm values
├── aws/                    # Phase 4: EKS/S3 IaC (Terraform / eksctl)
└── docs/                   # 아키텍처 문서
```

---

## 기술 스택

- **언어**: Python 3.11 (producer/consumer/Spark/Airflow DAG)
- **메시징**: Apache Kafka (로컬 KRaft, 클러스터는 Strimzi 오퍼레이터)
- **처리**: Apache Spark Structured Streaming (PySpark)
- **오케스트레이션**: Apache Airflow (KubernetesExecutor)
- **인프라**: Kubernetes (minikube/kind → AWS EKS), Terraform / eksctl
- **저장소**: S3 (Parquet), Postgres (집계 결과)
- **데이터 소스**: 한국은행 ECOS, KOSIS, 열린재정 OpenAPI
