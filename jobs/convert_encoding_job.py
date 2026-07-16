"""
Sample job: use the encoding_converter component to convert S3 objects
from Shift_JIS (CP932) to UTF-8 before the main ETL job consumes them.

s3://glue-sample-bucket/input_sjis/*      (CP932)
    -> s3://glue-sample-bucket/input_converted/*  (UTF-8)
"""
import sys

import boto3

sys.path.insert(0, "/home/glue_user/workspace/jobs/lib")
from encoding_converter import convert_s3_object  # noqa: E402

BUCKET = "glue-sample-bucket"
SRC_PREFIX = "input_sjis/"
DST_PREFIX = "input_converted/"
SRC_ENCODING = "cp932"
DST_ENCODING = "utf-8"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="ap-northeast-1",
)

resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=SRC_PREFIX)
objects = [o for o in resp.get("Contents", []) if not o["Key"].endswith("/")]

if not objects:
    print(f"No objects found under s3://{BUCKET}/{SRC_PREFIX}")
    sys.exit(1)

for obj in objects:
    src_key = obj["Key"]
    filename = src_key[len(SRC_PREFIX):]
    dst_key = f"{DST_PREFIX}{filename}"

    convert_s3_object(
        s3,
        BUCKET,
        src_key,
        dst_key,
        src_encoding=SRC_ENCODING,
        dst_encoding=DST_ENCODING,
    )
    print(f"Converted: s3://{BUCKET}/{src_key} ({SRC_ENCODING}) -> s3://{BUCKET}/{dst_key} ({DST_ENCODING})")

    # Read back the converted object to prove the text decodes correctly.
    converted_body = s3.get_object(Bucket=BUCKET, Key=dst_key)["Body"].read()
    preview = converted_body.decode(DST_ENCODING).splitlines()[:3]
    print("  preview:", " | ".join(preview))
