"""
Sample job: normalize fixed-length EBCDIC host files on S3 into UTF-8 CSV.

s3://<bucket>/input_ebcdic/*          (EBCDIC fixed-length, 40-byte records)
    -> s3://<bucket>/input_ebcdic_converted/*  (UTF-8 CSV)

Field-level decoding (including the special remapping of bytes 3-10) lives in
jobs/lib/fixed_length_ebcdic.py. Downstream Spark/Glue ETL can then read the
CSV without knowing about EBCDIC or byte offsets.

Runs unmodified both locally (against LocalStack, via --S3_ENDPOINT) and as
a real AWS Glue (Python shell) job (against actual S3, when --S3_ENDPOINT
is omitted).
"""
import sys

import boto3

try:
    from fixed_length_ebcdic import convert_s3_object
    from job_args import resolve_optional
except ImportError:
    sys.path.insert(0, "/home/glue_user/workspace/jobs/lib")
    from fixed_length_ebcdic import convert_s3_object
    from job_args import resolve_optional

BUCKET = resolve_optional(sys.argv, "BUCKET", "glue-sample-bucket")
S3_ENDPOINT = resolve_optional(sys.argv, "S3_ENDPOINT", "")
SRC_PREFIX = "input_ebcdic/"
DST_PREFIX = "input_ebcdic_converted/"

s3_kwargs = {}
if S3_ENDPOINT:
    # Local run against LocalStack: fixed dummy credentials and region.
    s3_kwargs.update(
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="ap-northeast-1",
    )
# On real AWS Glue, region and credentials come from the job's IAM role.
s3 = boto3.client("s3", **s3_kwargs)

resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=SRC_PREFIX)
objects = [o for o in resp.get("Contents", []) if not o["Key"].endswith("/")]

if not objects:
    print(f"No objects found under s3://{BUCKET}/{SRC_PREFIX}")
    sys.exit(1)

for obj in objects:
    src_key = obj["Key"]
    filename = src_key[len(SRC_PREFIX):]
    # Keep a stable CSV name even when the source has a host extension.
    if "." in filename:
        filename = filename.rsplit(".", 1)[0] + ".csv"
    else:
        filename = filename + ".csv"
    dst_key = f"{DST_PREFIX}{filename}"

    convert_s3_object(s3, BUCKET, src_key, dst_key)
    print(f"Normalized: s3://{BUCKET}/{src_key} -> s3://{BUCKET}/{dst_key}")

    preview = s3.get_object(Bucket=BUCKET, Key=dst_key)["Body"].read().decode("utf-8")
    preview_lines = preview.splitlines()[:4]
    print("  preview:", " | ".join(preview_lines))
