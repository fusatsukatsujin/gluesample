#!/usr/bin/env bash
# Runs the sample Glue ETL job inside the aws-glue-libs container.
# Usage: ./scripts/run-job.sh [input-prefix]   (default: input/)
set -euo pipefail

INPUT_PREFIX="${1:-input/}"

docker compose exec glue bash -lc "
  spark-submit /home/glue_user/workspace/jobs/etl_job.py \
    --JOB_NAME local-sample-job \
    --INPUT_PREFIX '${INPUT_PREFIX}' \
    --S3_ENDPOINT http://localstack:4566
"
