# aws — Phase 4: EKS로 승격 + S3 적재

같은 manifest를 AWS EKS에 배포하고 집계 결과를 S3(Parquet)로 적재한다.
**비용 관리가 핵심**: 하루만 켜서 스크린샷 남기고 `destroy`.

## 비용 감각

- EKS 컨트롤플레인 ~$0.10/h + t3.medium 노드 2개 ~$0.08/h → **시간당 약 $0.3**
- 하루 테스트 후 삭제하면 대략 **$5~7**. S3 저장 비용은 사실상 무시 가능.
- 개발 중 S3 호출은 **LocalStack** 으로 공짜 에뮬레이션하다가, 마지막에만 실제 S3 사용.

## 옵션 A — eksctl (빠름)

```bash
eksctl create cluster -f eksctl/cluster.yaml    # TODO 작성
# ... 배포 & 스크린샷 ...
eksctl delete cluster -f eksctl/cluster.yaml    # 반드시 삭제!
```

## 옵션 B — Terraform (IaC 어필용, 권장)

```bash
cd terraform
terraform init
terraform apply      # TODO: EKS 모듈 + S3 버킷 작성
# ...
terraform destroy    # 반드시 삭제!
```

> 권장: Terraform `terraform-aws-modules/eks` 모듈 사용. up/down을 코드로 재현 가능하게 두면
> 그 자체가 이력서의 "IaC 경험" 한 줄이 된다.

## Phase 4 체크리스트

- [ ] (개발) LocalStack으로 S3 sink 먼저 검증 — 무료
- [ ] EKS 클러스터 생성, `kubectl` 컨텍스트 전환 확인
- [ ] Phase 2~3 manifest를 그대로 EKS에 적용 (이미지는 ECR push)
- [ ] Spark 집계 결과가 실제 S3 버킷에 Parquet으로 쌓이는지 확인 + 스크린샷
- [ ] **`destroy` 로 자원 삭제** (비용 차단), 청구서 확인
