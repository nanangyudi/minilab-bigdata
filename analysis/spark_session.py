from __future__ import annotations

import os
from pyspark.sql import SparkSession


def create_spark_session(app_name: str = "Minilab Big Data") -> SparkSession:
    """Buat SparkSession dengan konfigurasi S3A untuk koneksi ke MinIO.

    Variabel environment yang dibutuhkan (dari .env):
        MINIO_ROOT_USER     — MinIO access key
        MINIO_ROOT_PASSWORD — MinIO secret key
        MINIO_ENDPOINT      — MinIO endpoint (default: http://minio:9000)
    """
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    access_key = os.environ["MINIO_ROOT_USER"]
    secret_key = os.environ["MINIO_ROOT_PASSWORD"]

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        # JAR hadoop-aws + aws-sdk diunduh otomatis dari Maven Central saat pertama kali dijalankan
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.262")
        # Konfigurasi S3A untuk MinIO
        .config("spark.hadoop.fs.s3a.endpoint", endpoint)
        .config("spark.hadoop.fs.s3a.access.key", access_key)
        .config("spark.hadoop.fs.s3a.secret.key", secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        # Nonaktifkan fitur yang tidak dibutuhkan di minilab
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark
