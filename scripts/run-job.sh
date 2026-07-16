#!/usr/bin/env bash
# Runs the sample Glue ETL job inside the aws-glue-libs container.
set -euo pipefail

docker compose exec glue bash -lc '
  spark-submit /home/glue_user/workspace/jobs/etl_job.py --JOB_NAME local-sample-job
'
