# aws — Phase 4: EKS로 승격 + S3 적재

Phase 2~3의 manifest를 그대로 AWS EKS에 올리고, Spark 집계 결과를 S3(Parquet)로 적재한다.
**비용 관리가 핵심**: 하루만 켜서 스크린샷 남기고 `destroy`.

## 파일

```
aws/
├── terraform/                  # 권장 (IaC 어필)
│   ├── versions.tf             # provider 버전
│   ├── variables.tf            # region, cluster_name, bucket_name ...
│   ├── main.tf                 # VPC + EKS + S3 + S3접근 IAM 정책
│   ├── outputs.tf              # kubeconfig 명령, 버킷, s3a 경로
│   └── terraform.tfvars.example
└── eksctl/cluster.yaml         # 빠르게 띄울 때 대안
```

## 비용 감각

- EKS 컨트롤플레인 ~$0.10/h + t3.medium 2대 ~$0.08/h + NAT ~$0.05/h → **시간당 약 $0.25~0.3**
- 하루 테스트 후 삭제 시 대략 **$5~7**. S3 저장은 사실상 무시 가능.
- 개발 중 S3 호출은 **LocalStack** 으로 공짜 에뮬레이션하다가, 마지막에만 실제 S3 사용.

## 옵션 A — Terraform (권장)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # bucket_name 을 유일하게 수정
terraform init
terraform apply                                 # ⚠️ 과금 시작
$(terraform output -raw configure_kubectl)      # kubeconfig 설정
# ... Phase 2~3 배포 & 검증 & 스크린샷 ...
terraform destroy                               # ⚠️ 반드시 삭제!
```

## 옵션 B — eksctl

```bash
eksctl create cluster -f eksctl/cluster.yaml
# ...
eksctl delete cluster -f eksctl/cluster.yaml    # 반드시 삭제!
```

## EKS에 올린 뒤

1. **이미지 ECR push**: `econ-producer:0.1`, `econ-spark:0.1` 를 ECR로 push하고 manifest의 image 경로 교체.
2. **Phase 2~3 그대로 apply**: `k8s/` manifest와 `airflow/` helm은 클러스터만 EKS로 바뀔 뿐 동일.
3. **Spark → S3 적재**: SparkApplication에 `SINK=parquet`, `OUTPUT_PATH=s3a://<버킷>/agg` 주입.
   - 노드 IAM에 S3 정책이 붙어 있음(main.tf). 더 세밀하게는 IRSA로 spark SA에 역할 연결.
   - s3a 사용 시 `hadoop-aws`, `aws-java-sdk-bundle` 패키지를 deps에 추가.

## Phase 4 체크리스트

- [ ] (개발) LocalStack으로 S3 sink 먼저 검증 — 무료
- [ ] `terraform apply` 로 EKS+S3 생성, `kubectl get nodes` 확인
- [ ] 이미지 ECR push, manifest image 경로 교체
- [ ] Phase 2~3 배포, Spark 집계 결과가 S3 버킷에 Parquet으로 쌓이는지 + 스크린샷
- [ ] **`terraform destroy` 로 자원 삭제** (비용 차단), 청구서 확인
