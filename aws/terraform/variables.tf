variable "region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2" # 서울
}

variable "cluster_name" {
  description = "EKS 클러스터 이름"
  type        = string
  default     = "econ-eks"
}

variable "cluster_version" {
  description = "EKS 쿠버네티스 버전"
  type        = string
  default     = "1.31"
}

variable "bucket_name" {
  description = "집계 결과 적재용 S3 버킷 (전 세계 유일해야 함)"
  type        = string
}

variable "instance_type" {
  description = "노드 인스턴스 타입"
  type        = string
  default     = "t3.medium"
}
