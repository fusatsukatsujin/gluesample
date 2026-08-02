"""Demo: fixed-length EBCDIC with a special conversion on bytes 3-10 only.

Layering (matches the discussion in this repo):

  1) Host binary (EBCDIC fixed-length)
        -> jobs/lib/fixed_length_ebcdic.py   # normalize here
  2) UTF-8 CSV / row dicts
        -> Spark/Glue (column transforms, agg)  # illustrated below

Run from repo root:

  python3 tmp/demo_ebcdic_fixed_length.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "jobs" / "lib"
sys.path.insert(0, str(LIB))

from fixed_length_ebcdic import (  # noqa: E402
    build_record,
    parse_records,
    records_to_csv_lines,
    remap_customer_code,
)


def build_sample_host_file() -> bytes:
    """Three host records. Codes CUST0001/OLD99999 are remapped; CUST0099 is not."""
    return b"".join(
        [
            build_record("01", "CUST0001", "TARO YAMADA", 1500),
            build_record("01", "OLD99999", "HANAKO SUZUKI", 200),
            build_record("01", "CUST0099", "ICHIRO TANAKA", 80),
        ]
    )


def spark_side_illustration(rows: list[dict]) -> None:
    """Show what a Glue/Spark job would do *after* normalization.

    Real Spark (for reference — needs a Glue/Spark runtime):

        df = spark.read.option("header", True).csv(path)
        df = df.withColumn("amount", F.col("amount").cast("int"))
        # further column-only business rules if needed:
        # df = df.withColumn("customer_code", F.upper(F.col("customer_code")))
        summary = df.groupBy("customer_code").agg(F.sum("amount").alias("total"))

    Here we mirror that with plain Python so the demo runs without Spark.
    """
    print("--- Spark-side illustration (plain Python stand-in) ---")
    print("Input columns already UTF-8; EBCDIC/byte offsets are gone.")
    totals: dict[str, int] = {}
    for row in rows:
        code = row["customer_code"]
        totals[code] = totals.get(code, 0) + int(row["amount"])
    for code, total in sorted(totals.items()):
        print(f"  {code}: total_amount={total}")


def main() -> None:
    body = build_sample_host_file()
    print(f"Host file size: {len(body)} bytes ({len(body) // 40} records)")
    print(f"Raw bytes[0:10] (record_type + customer_code): {body[0:10]!r}")
    print()

    rows = list(parse_records(body))
    print("--- After field-level normalize (bytes 3-10 remapped) ---")
    for row in rows:
        print(row)

    # Highlight the special conversion on bytes 3-10.
    print()
    print("--- Special conversion on customer_code (bytes 3-10) ---")
    for host_code, expected in [
        ("CUST0001", "C-001"),
        ("OLD99999", "C-999"),
        ("CUST0099", "CUST0099"),  # unmapped: pass through
    ]:
        print(f"  {host_code!r} -> {remap_customer_code(host_code)!r} (expect {expected!r})")
        assert remap_customer_code(host_code) == expected

    assert rows[0]["customer_code"] == "C-001"
    assert rows[1]["customer_code"] == "C-999"
    assert rows[2]["customer_code"] == "CUST0099"
    assert rows[0]["amount"] == 1500

    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / "host_normalized.csv"
    csv_path.write_text(records_to_csv_lines(rows), encoding="utf-8")
    print()
    print(f"Wrote UTF-8 CSV for Spark/Glue: {csv_path}")
    print(csv_path.read_text(encoding="utf-8"))

    spark_side_illustration(rows)
    print()
    print("OK: normalize owns EBCDIC + byte 3-10 remapping; Spark owns columnar ETL.")


if __name__ == "__main__":
    main()
