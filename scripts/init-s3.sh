#!/usr/bin/env bash
# Creates the sample S3 bucket in LocalStack and uploads the input CSV.
set -euo pipefail

BUCKET="glue-sample-bucket"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker compose exec -T localstack awslocal s3 mb "s3://${BUCKET}" || true

docker compose cp "${SCRIPT_DIR}/../data/input/sales.csv" localstack:/tmp/sales.csv
docker compose exec -T localstack awslocal s3 cp /tmp/sales.csv "s3://${BUCKET}/input/sales.csv"

# Shift_JIS (CP932) sample data, used by the encoding conversion component.
docker compose cp "${SCRIPT_DIR}/../data/input_sjis/sales_sjis.csv" localstack:/tmp/sales_sjis.csv
docker compose exec -T localstack awslocal s3 cp /tmp/sales_sjis.csv "s3://${BUCKET}/input_sjis/sales_sjis.csv"

echo "Uploaded input data:"
docker compose exec -T localstack awslocal s3 ls "s3://${BUCKET}/input/"
docker compose exec -T localstack awslocal s3 ls "s3://${BUCKET}/input_sjis/"
