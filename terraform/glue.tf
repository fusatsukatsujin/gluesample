resource "aws_glue_job" "etl" {
  name              = "${var.project_name}-etl-job"
  role_arn          = aws_iam_role.glue_job.arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.data.id}/${aws_s3_object.etl_job_script.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--BUCKET"              = aws_s3_bucket.data.id
    "--INPUT_PREFIX"        = "input/"
    "--extra-py-files"      = "s3://${aws_s3_bucket.data.id}/${aws_s3_object.job_args_lib.key}"
    "--TempDir"             = "s3://${aws_s3_bucket.data.id}/tmp/"
    "--job-bookmark-option" = "job-bookmark-disable"
    "--job-language"        = "python"
  }
}

resource "aws_glue_job" "convert_encoding" {
  name         = "${var.project_name}-convert-encoding-job"
  role_arn     = aws_iam_role.glue_job.arn
  max_capacity = 0.0625 # smallest Python shell size; this job does not use Spark

  command {
    name            = "pythonshell"
    script_location = "s3://${aws_s3_bucket.data.id}/${aws_s3_object.convert_encoding_job_script.key}"
    python_version  = "3.9"
  }

  default_arguments = {
    "--BUCKET" = aws_s3_bucket.data.id
    "--extra-py-files" = join(",", [
      "s3://${aws_s3_bucket.data.id}/${aws_s3_object.job_args_lib.key}",
      "s3://${aws_s3_bucket.data.id}/${aws_s3_object.encoding_converter_lib.key}",
    ])
  }
}
