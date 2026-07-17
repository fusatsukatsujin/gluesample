#!/usr/bin/env bash
# Runs the sample encoding-conversion job (Shift_JIS -> UTF-8) against
# s3://glue-sample-bucket/input_sjis/, writing results to input_converted/.
set -euo pipefail

docker compose exec glue bash -lc '
  python3 /home/glue_user/workspace/jobs/convert_encoding_job.py --S3_ENDPOINT http://localstack:4566
'
