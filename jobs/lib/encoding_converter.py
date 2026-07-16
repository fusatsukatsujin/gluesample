"""Reusable component: convert the character encoding of an S3 text object.

Typical use case: a legacy system exports CSV files in Shift_JIS (CP932),
but downstream Spark/Glue processing expects UTF-8. This module converts
such objects in place on S3 before the main ETL job reads them.
"""


def convert_encoding(body: bytes, src_encoding: str, dst_encoding: str, errors: str = "strict") -> bytes:
    """Decode bytes using src_encoding and re-encode using dst_encoding."""
    text = body.decode(src_encoding, errors=errors)
    return text.encode(dst_encoding, errors=errors)


def convert_s3_object(
    s3_client,
    bucket: str,
    src_key: str,
    dst_key: str,
    src_encoding: str = "cp932",
    dst_encoding: str = "utf-8",
    errors: str = "strict",
) -> str:
    """Read src_key from S3, convert its encoding, and write it to dst_key."""
    obj = s3_client.get_object(Bucket=bucket, Key=src_key)
    body = obj["Body"].read()
    converted = convert_encoding(body, src_encoding, dst_encoding, errors=errors)
    s3_client.put_object(Bucket=bucket, Key=dst_key, Body=converted)
    return dst_key
