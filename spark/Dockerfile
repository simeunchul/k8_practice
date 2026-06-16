# Phase 2에서 Spark Operator가 제출할 이미지.
# kafka connector jar는 SparkApplication spec.deps.packages로 주입하거나 여기서 미리 받아둔다.
FROM apache/spark:3.5.1

USER root
COPY jobs/ /opt/spark/work-dir/jobs/

# (선택) connector를 이미지에 미리 포함시키고 싶으면 아래 주석 해제
# RUN /opt/spark/bin/spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
#       --class org.apache.spark.deploy.SparkSubmit --version || true

USER spark
