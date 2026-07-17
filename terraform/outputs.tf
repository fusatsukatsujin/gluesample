output "bucket_name" {
  description = "S3 bucket holding scripts, input data, and job output."
  value       = aws_s3_bucket.data.id
}

output "etl_job_name" {
  description = "Name of the main ETL Glue job."
  value       = aws_glue_job.etl.name
}

output "convert_encoding_job_name" {
  description = "Name of the Shift_JIS -> UTF-8 conversion Glue job."
  value       = aws_glue_job.convert_encoding.name
}

output "run_etl_job_command" {
  description = "AWS CLI command to start the ETL job."
  value       = "aws glue start-job-run --job-name ${aws_glue_job.etl.name} --region ${var.aws_region}"
}

output "run_convert_encoding_job_command" {
  description = "AWS CLI command to start the encoding conversion job."
  value       = "aws glue start-job-run --job-name ${aws_glue_job.convert_encoding.name} --region ${var.aws_region}"
}
