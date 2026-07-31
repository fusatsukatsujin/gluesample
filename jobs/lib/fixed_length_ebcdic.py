"""Normalize fixed-length EBCDIC host records into UTF-8 row dicts.

Motivation
----------
Host files often need field-level (not whole-file) decoding:

  bytes 1-2   : record type   (EBCDIC)
  bytes 3-10  : customer code (EBCDIC + *legacy code remapping*)
  bytes 11-30 : customer name (EBCDIC)
  bytes 31-40 : amount        (EBCDIC digits)

Only the customer-code slice gets an extra business conversion; other
fields are decoded with the same CCSID but no remapping. Downstream
Spark/Glue jobs then consume a plain UTF-8 CSV / list of dicts — they
do not need to know about EBCDIC or byte offsets.

Positions are 1-based inclusive, matching typical host layout docs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Optional

# IBM US EBCDIC — available in the Python stdlib; fine for alphanumeric demos.
# Japanese host data would often use cp930 / cp939 instead (same slicing idea).
DEFAULT_ENCODING = "cp037"
EBCDIC_SPACE = b"\x40"
RECORD_LENGTH = 40

# Legacy host codes -> canonical codes used by downstream systems.
LEGACY_CUSTOMER_CODE_MAP = {
    "CUST0001": "C-001",
    "CUST0002": "C-002",
    "OLD99999": "C-999",
}


@dataclass(frozen=True)
class FieldSpec:
    """One fixed-length field. start/end are 1-based inclusive byte positions."""

    name: str
    start: int
    end: int
    encoding: str = DEFAULT_ENCODING
    transform: Optional[Callable[[str], object]] = None

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def extract(self, record: bytes) -> object:
        raw = record[self.start - 1 : self.end]
        text = raw.decode(self.encoding).replace("\x00", "").strip()
        if self.transform is None:
            return text
        return self.transform(text)


def remap_customer_code(code: str) -> str:
    """Special conversion applied only to bytes 3-10."""
    return LEGACY_CUSTOMER_CODE_MAP.get(code, code)


def parse_amount(text: str) -> int:
    digits = text.strip()
    if not digits:
        return 0
    return int(digits)


# Default layout for this sample (40-byte records).
DEFAULT_LAYOUT: tuple[FieldSpec, ...] = (
    FieldSpec("record_type", 1, 2),
    FieldSpec("customer_code", 3, 10, transform=remap_customer_code),
    FieldSpec("customer_name", 11, 30),
    FieldSpec("amount", 31, 40, transform=parse_amount),
)


def parse_record(record: bytes, layout: Iterable[FieldSpec] = DEFAULT_LAYOUT) -> dict:
    """Parse one fixed-length record into a UTF-8-oriented dict."""
    if len(record) != RECORD_LENGTH:
        raise ValueError(f"expected {RECORD_LENGTH}-byte record, got {len(record)}")
    return {field.name: field.extract(record) for field in layout}


def parse_records(body: bytes, layout: Iterable[FieldSpec] = DEFAULT_LAYOUT) -> Iterator[dict]:
    """Split a binary body into RECORD_LENGTH chunks and parse each."""
    if len(body) % RECORD_LENGTH != 0:
        raise ValueError(
            f"body length {len(body)} is not a multiple of record length {RECORD_LENGTH}"
        )
    layout = tuple(layout)
    for offset in range(0, len(body), RECORD_LENGTH):
        yield parse_record(body[offset : offset + RECORD_LENGTH], layout)


def _pad_ebcdic(text: str, length: int, encoding: str = DEFAULT_ENCODING) -> bytes:
    raw = text.encode(encoding)
    if len(raw) > length:
        raise ValueError(f"{text!r} encodes to {len(raw)} bytes, max {length}")
    return raw + EBCDIC_SPACE * (length - len(raw))


def _ebcdic_digits(value: int, length: int, encoding: str = DEFAULT_ENCODING) -> bytes:
    return str(value).zfill(length).encode(encoding)


def build_record(
    record_type: str,
    customer_code: str,
    customer_name: str,
    amount: int,
    encoding: str = DEFAULT_ENCODING,
) -> bytes:
    """Build one sample host record (useful for demos and tests)."""
    parts = [
        _pad_ebcdic(record_type, 2, encoding),
        _pad_ebcdic(customer_code, 8, encoding),
        _pad_ebcdic(customer_name, 20, encoding),
        _ebcdic_digits(amount, 10, encoding),
    ]
    record = b"".join(parts)
    assert len(record) == RECORD_LENGTH
    return record


def records_to_csv_lines(rows: Iterable[dict]) -> str:
    """Serialize parsed rows to a UTF-8 CSV string (header + data)."""
    fieldnames = [f.name for f in DEFAULT_LAYOUT]
    lines = [",".join(fieldnames)]
    for row in rows:
        lines.append(
            ",".join(str(row[name]) for name in fieldnames)
        )
    return "\n".join(lines) + "\n"


def normalize_to_csv(body: bytes) -> bytes:
    """Parse an EBCDIC fixed-length body and return UTF-8 CSV bytes."""
    rows = list(parse_records(body))
    return records_to_csv_lines(rows).encode("utf-8")


def convert_s3_object(s3_client, bucket: str, src_key: str, dst_key: str) -> str:
    """Read an EBCDIC fixed-length object from S3 and write UTF-8 CSV to dst_key."""
    obj = s3_client.get_object(Bucket=bucket, Key=src_key)
    body = obj["Body"].read()
    csv_body = normalize_to_csv(body)
    s3_client.put_object(Bucket=bucket, Key=dst_key, Body=csv_body)
    return dst_key
