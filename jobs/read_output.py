"""Reads back the job output from S3 (LocalStack) and prints it, to verify the ETL job."""
from pyspark.context import SparkContext
from pyspark.sql import SparkSession

BUCKET = "glue-sample-bucket"
OUTPUT_PATH = f"s3a://{BUCKET}/output/sales_summary/"

sc = SparkContext.getOrCreate()
hadoop_conf = sc._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.endpoint", "http://localstack:4566")
hadoop_conf.set("fs.s3a.access.key", "test")
hadoop_conf.set("fs.s3a.secret.key", "test")
hadoop_conf.set("fs.s3a.path.style.access", "true")
hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

spark = SparkSession.builder.getOrCreate()
df = spark.read.parquet(OUTPUT_PATH)
df.show(truncate=False)
