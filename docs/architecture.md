# 아키텍처

## 데이터 흐름

```
┌──────────────┐   produce   ┌─────────────┐   subscribe   ┌──────────────────┐   write   ┌─────────────┐
│  producer    │ ──────────▶ │   Kafka     │ ────────────▶ │ Spark Structured │ ────────▶ │ S3 (Parquet)│
│ ECOS/KOSIS   │  JSON event │ econ.       │  event stream │ Streaming        │  windowed │ + Postgres  │
│ poller       │             │ indicators  │               │ (윈도우 집계)     │   agg     │ (집계결과)   │
└──────────────┘             └─────────────┘               └──────────────────┘           └─────────────┘
        ▲                                                            ▲
        │ schedule                                                   │ submit
        └──────────────── Airflow (KubernetesExecutor) ──────────────┘

                    ── 전 구성요소가 Kubernetes 위에서 동작 ──
        로컬: minikube / kind          →          AWS: EKS + ECR + S3
```

## 컴포넌트별 책임

| 컴포넌트 | 역할 | 기술 |
|----------|------|------|
| producer | 경제지표 API 폴링 → 이벤트 발행 | Python, confluent-kafka |
| Kafka | 이벤트 버퍼링·내구성·재처리 | Strimzi (K8s) |
| Spark | event-time 윈도우 집계, 정확히 한 번 | PySpark Structured Streaming |
| 저장소 | 원천 적재(S3 Parquet) + 집계 결과(Postgres) | S3, Postgres |
| Airflow | 수집/집계 스케줄·백필·의존성 | KubernetesExecutor |
| 인프라 | 전체 배포·확장 | K8s → EKS, Terraform |

## 이벤트 스키마 (`econ.indicators`)

```json
{
  "indicator": "base_rate",
  "name": "기준금리",
  "value": 3.5,
  "ts": 1718500000000,
  "source": "ecos"
}
```

## 단계별 진화

1. **Phase 0** — producer/Kafka/consumer를 docker-compose로. (메시징 기초)
2. **Phase 1** — consumer를 Spark로 교체. (스트림 처리)
3. **Phase 2** — 전부 로컬 K8s로. (오케스트레이션·배포)
4. **Phase 3** — Airflow로 스케줄링. (워크플로우)
5. **Phase 4** — EKS+S3로 승격. (클라우드)
