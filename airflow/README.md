# airflow — Phase 3: KubernetesExecutor 오케스트레이션

Airflow를 K8s에 올리고 **KubernetesExecutor**로 태스크마다 파드를 띄운다.
(면접관이 콕 집어 추천한 구성: "Airflow를 minikube/KubernetesExecutor에 올려보기")

## 역할

- **상시 스트리밍**(Spark)은 Phase 2의 SparkApplication이 계속 처리.
- **이 DAG**는 스케줄 배치/백필 담당 — 매시간 ECOS를 한 번 수집하고 배치 집계를 트리거.

## 설치

```bash
helm repo add apache-airflow https://airflow.apache.org && helm repo update
helm install airflow apache-airflow/airflow -n econ -f values.yaml
```

`values.yaml` 핵심:
- `executor: KubernetesExecutor` (Redis/Flower 비활성)
- DAG 전달: **gitSync** 로 이 레포의 `airflow/dags` 동기화 → `repo` 를 본인 레포로 바꿔야 함
- 첫 계정 admin/admin (토이용)

## 접속

```bash
kubectl port-forward svc/airflow-webserver 8080:8080 -n econ
# http://localhost:8080  (admin / admin)
```

## DAG: `dags/ecos_ingestion_dag.py`

```
ingest_ecos (econ-producer 파드)  ──▶  run_spark_agg (econ-spark 파드, SINK=parquet)
```

- 두 태스크 모두 `KubernetesPodOperator` → KubernetesExecutor가 독립 파드로 실행
- ECOS 키는 `econ-secrets` Secret에서 env로 주입 (k8s/producer/secret.example.yaml 참고)

## Phase 3 체크리스트

- [ ] 웹UI 접속, DAG `ecos_ingestion` 가 보이는지 (gitSync 동기화 확인)
- [ ] DAG 트리거 → `kubectl get pods -n econ -w` 로 태스크 파드가 떴다 사라지는지
- [ ] `ingest → aggregate` 의존성이 순서대로 실행되는지
- [ ] `catchup=True` + 과거 `start_date` 로 백필 한 번 돌려보기
