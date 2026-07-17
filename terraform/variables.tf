variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Prefix used for resource names."
  type        = string
  default     = "glue-sample"
}

variable "bucket_name" {
  description = "S3 bucket name for scripts/data. Must be globally unique. Leave empty to auto-generate one."
  type        = string
  default     = ""
}
