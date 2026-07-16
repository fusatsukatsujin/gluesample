#!/usr/bin/env bash
# Lists the job's output files and prints the resulting Parquet data.
set -euo pipefail

BUCKET="glue-sample-bucket"

echo "Output files:"
docker compose exec -T localstack awslocal s3 ls --recursive "s3://${BUCKET}/output/"

echo
echo "Output contents:"
docker compose exec glue bash -lc '
  spark-submit /home/glue_user/workspace/jobs/read_output.py
'
