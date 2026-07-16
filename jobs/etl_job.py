"""
AWS Glue ETL sample job (runs locally against LocalStack S3).

Reads sales.csv from S3, computes per-product totals, and writes the
result back to S3 as Parquet using the standard GlueContext DynamicFrame API.
"""
import sys

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

BUCKET = "glue-sample-bucket"
INPUT_PATH = f"s3a://{BUCKET}/input/"
OUTPUT_PATH = f"s3a://{BUCKET}/output/sales_summary/"

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext.getOrCreate()

# Point the Hadoop S3A connector at LocalStack instead of real AWS S3.
hadoop_conf = sc._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.endpoint", "http://localstack:4566")
hadoop_conf.set("fs.s3a.access.key", "test")
hadoop_conf.set("fs.s3a.secret.key", "test")
hadoop_conf.set("fs.s3a.path.style.access", "true")
hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# --- Extract ---
source_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [INPUT_PATH]},
    format="csv",
    format_options={"withHeader": True, "separator": ","},
)

# --- Transform ---
df = source_dyf.toDF()
df = (
    df.withColumn("quantity", F.col("quantity").cast("int"))
    .withColumn("price", F.col("price").cast("double"))
    .withColumn("total_amount", F.col("quantity") * F.col("price"))
    .filter(F.col("quantity") > 0)
)

summary_df = df.groupBy("product").agg(
    F.sum("quantity").alias("total_quantity"),
    F.round(F.sum("total_amount"), 2).alias("total_sales"),
).orderBy("product")

summary_df.show(truncate=False)

result_dyf = DynamicFrame.fromDF(summary_df, glueContext, "result_dyf")

# --- Load ---
glueContext.write_dynamic_frame.from_options(
    frame=result_dyf,
    connection_type="s3",
    connection_options={"path": OUTPUT_PATH},
    format="parquet",
)

job.commit()
print(f"Job finished. Output written to {OUTPUT_PATH}")
