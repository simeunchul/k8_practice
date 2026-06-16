output "cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "configure_kubectl" {
  description = "kubeconfig 설정 명령"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "s3_bucket" {
  description = "데이터 적재 버킷"
  value       = aws_s3_bucket.data.bucket
}

output "s3_path_for_spark" {
  description = "Spark OUTPUT_PATH 로 쓸 s3a 경로"
  value       = "s3a://${aws_s3_bucket.data.bucket}/agg"
}
