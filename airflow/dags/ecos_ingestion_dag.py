"""Phase 3 — KubernetesExecutor로 수집/집계를 오케스트레이션하는 DAG 골격.

KubernetesPodOperator는 태스크를 독립 파드로 실행한다.
TODO: 이미지 이름/네임스페이스/시크릿/리소스 채우기.
"""
from datetime import datetime, timedelta

from airflow import DAG

try:
    from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
except ImportError:  # 로컬에 provider 미설치 시 import만 방어
    KubernetesPodOperator = None

default_args = {
    "owner": "econ",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="ecos_ingestion",
    description="ECOS 수집 → Spark 집계 (KubernetesExecutor)",
    default_args=default_args,
    schedule="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,        # 백필 실습 때 True 로
    tags=["econ", "phase3"],
) as dag:

    ingest = KubernetesPodOperator(
        task_id="ingest_ecos",
        name="ingest-ecos",
        namespace="econ",
        image="econ-producer:0.1",   # TODO: 레지스트리 경로
        arguments=[],                 # 실수집 모드 (--mock 제거)
        # env_vars=[k8s.V1EnvVar(name="ECOS_API_KEY", value_from=...secret...)],
        get_logs=True,
    )

    aggregate = KubernetesPodOperator(
        task_id="run_spark_agg",
        name="run-spark-agg",
        namespace="econ",
        image="econ-spark:0.1",       # TODO: Spark 잡 이미지 또는 SparkKubernetesOperator로 교체
        get_logs=True,
    )

    ingest >> aggregate
