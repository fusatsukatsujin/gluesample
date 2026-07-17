resource "aws_s3_bucket" "data" {
  bucket = local.bucket_name

  # Job runs write output/tmp objects that Terraform doesn't manage
  # (output/, input_converted/, tmp/). Without this, `terraform destroy`
  # fails with BucketNotEmpty once a job has run.
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Glue job scripts ---

resource "aws_s3_object" "etl_job_script" {
  bucket = aws_s3_bucket.data.id
  key    = "scripts/etl_job.py"
  source = "${path.module}/../jobs/etl_job.py"
  etag   = filemd5("${path.module}/../jobs/etl_job.py")
}

resource "aws_s3_object" "convert_encoding_job_script" {
  bucket = aws_s3_bucket.data.id
  key    = "scripts/convert_encoding_job.py"
  source = "${path.module}/../jobs/convert_encoding_job.py"
  etag   = filemd5("${path.module}/../jobs/convert_encoding_job.py")
}

resource "aws_s3_object" "job_args_lib" {
  bucket = aws_s3_bucket.data.id
  key    = "scripts/lib/job_args.py"
  source = "${path.module}/../jobs/lib/job_args.py"
  etag   = filemd5("${path.module}/../jobs/lib/job_args.py")
}

resource "aws_s3_object" "encoding_converter_lib" {
  bucket = aws_s3_bucket.data.id
  key    = "scripts/lib/encoding_converter.py"
  source = "${path.module}/../jobs/lib/encoding_converter.py"
  etag   = filemd5("${path.module}/../jobs/lib/encoding_converter.py")
}

# --- Sample input data ---

resource "aws_s3_object" "sample_input" {
  bucket = aws_s3_bucket.data.id
  key    = "input/sales.csv"
  source = "${path.module}/../data/input/sales.csv"
  etag   = filemd5("${path.module}/../data/input/sales.csv")
}

resource "aws_s3_object" "sample_input_sjis" {
  bucket = aws_s3_bucket.data.id
  key    = "input_sjis/sales_sjis.csv"
  source = "${path.module}/../data/input_sjis/sales_sjis.csv"
  etag   = filemd5("${path.module}/../data/input_sjis/sales_sjis.csv")
}
