#!/usr/bin/env bash
# Runs the sample EBCDIC fixed-length normalization job against
# s3://glue-sample-bucket/input_ebcdic/, writing UTF-8 CSV to
# input_ebcdic_converted/.
set -euo pipefail

docker compose exec glue bash -lc '
  python3 /home/glue_user/workspace/jobs/convert_ebcdic_job.py --S3_ENDPOINT http://localstack:4566
'
