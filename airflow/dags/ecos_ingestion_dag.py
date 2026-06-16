"""Phase 3 — KubernetesExecutor 오케스트레이션 DAG.

역할 분담:
  - 상시 스트리밍(Spark)은 Phase 2의 SparkApplication이 계속 돌고 있음.
  - 이 DAG는 "스케줄 배치/백필"을 담당 — 매시간 ECOS 최신값을 한 번 수집(batch)하고,
    이어서 배치 집계 잡을 트리거한다.

각 태스크는 KubernetesExecutor 환경에서 독립 파드(KubernetesPodOperator)로 실행된다.
"""
from datetime import datetime, timedelta

from airflow import DAG

try:
    from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
    from airflow.providers.cncf.kubernetes.secret import Secret
    from kubernetes.client import models as k8s
except ImportError:  # 로컬 lint 시 provider 미설치 방어
    KubernetesPodOperator = None
    Secret = None
    k8s = None

NAMESPACE = "econ"
BOOTSTRAP = "econ-kafka-kafka-bootstrap:9092"

default_args = {
    "owner": "econ",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

# ECOS 키를 Secret(econ-secrets)에서 환경변수로 주입
ecos_secret = (
    Secret(deploy_type="env", deploy_target="ECOS_API_KEY",
           secret="econ-secrets", key="ECOS_API_KEY")
    if Secret else None
)

with DAG(
    dag_id="ecos_ingestion",
    description="ECOS 배치 수집 → 배치 집계 (KubernetesExecutor)",
    default_args=default_args,
    schedule="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,        # 과거 백필 실습 시 True (그리고 start_date 조정)
    max_active_runs=1,
    tags=["econ", "phase3"],
) as dag:

    ingest = KubernetesPodOperator(
        task_id="ingest_ecos",
        name="ingest-ecos",
        namespace=NAMESPACE,
        image="econ-producer:0.1",
        # 실수집(배치) 모드. mock으로 빠르게 테스트하려면 arguments=["--mock"]
        arguments=[],
        env_vars=[
            k8s.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value=BOOTSTRAP),
            k8s.V1EnvVar(name="KAFKA_TOPIC", value="econ.indicators"),
        ] if k8s else None,
        secrets=[ecos_secret] if ecos_secret else None,
        get_logs=True,
        is_delete_operator_pod=True,
    )

    aggregate = KubernetesPodOperator(
        task_id="run_spark_agg",
        name="run-spark-agg",
        namespace=NAMESPACE,
        image="econ-spark:0.1",
        # 배치 집계: SINK=parquet 로 S3/로컬에 적재 (Phase 4에서 s3a 경로)
        env_vars=[
            k8s.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value=BOOTSTRAP),
            k8s.V1EnvVar(name="SINK", value="parquet"),
        ] if k8s else None,
        cmds=["/opt/spark/bin/spark-submit"],
        arguments=[
            "--conf", "spark.jars.ivy=/tmp/.ivy2",
            "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
            "/opt/spark/work-dir/jobs/streaming_aggregation.py",
        ],
        get_logs=True,
        is_delete_operator_pod=True,
    )

    ingest >> aggregate
