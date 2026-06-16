# Phase 4 — EKS + S3. 토이용 최소 구성.
# 비용 주의: apply 하면 과금 시작. 끝나면 반드시 `terraform destroy`.

data "aws_availability_zones" "available" {
  state = "available"
}

# ── VPC ───────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)

  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true # 토이라 NAT 1개로 비용 절감

  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}

# ── EKS ───────────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    default = {
      instance_types = [var.instance_type]
      min_size       = 2
      max_size       = 3
      desired_size   = 2

      # 노드가 S3 버킷에 접근하도록 정책 부착 (Spark s3a 적재용)
      iam_role_additional_policies = {
        s3 = aws_iam_policy.s3_access.arn
      }
    }
  }
}

# ── S3 (집계 결과 적재) ────────────────────────────────────
resource "aws_s3_bucket" "data" {
  bucket        = var.bucket_name
  force_destroy = true # 토이: destroy 시 객체까지 삭제
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_policy" "s3_access" {
  name        = "${var.cluster_name}-s3-access"
  description = "Spark가 데이터 버킷에 읽고 쓰도록 허용"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
      }
    ]
  })
}
