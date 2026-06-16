# airflow — Phase 3: KubernetesExecutor 오케스트레이션

Airflow를 K8s에 올리고 **KubernetesExecutor**로 태스크마다 파드를 띄운다.
(면접관이 콕 집어 추천한 구성: "Airflow를 minikube/KubernetesExecutor에 올려보기")

## 설치 (공식 Helm 차트)

```bash
helm repo add apache-airflow https://airflow.apache.org
helm install airflow apache-airflow/airflow -n econ -f values.yaml   # TODO: values.yaml 작성
```

`values.yaml` 핵심:
- `executor: KubernetesExecutor`
- DAG 동기화: gitSync 또는 이미지 굽기
- ECOS 키는 Secret으로 주입

## DAG

- `dags/ecos_ingestion_dag.py` — `KubernetesPodOperator` 로 producer 파드를 스케줄 실행하고,
  Spark 잡 제출/백필을 오케스트레이션하는 골격.

## Phase 3 체크리스트

- [ ] Airflow 웹UI 접속 (`kubectl port-forward svc/airflow-webserver 8080:8080`)
- [ ] KubernetesExecutor로 태스크가 파드로 뜨는지 (`kubectl get pods -w`)
- [ ] producer 수집 → Spark 집계 의존성을 DAG로 연결
- [ ] 과거 구간 백필(`catchup=True`) 한 번 돌려보기
