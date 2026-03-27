from __future__ import annotations

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


def load_latest_partition(
    spark: SparkSession,
    bucket: str,
    zone: str,
    dataset: str,
    filename: str,
) -> DataFrame:
    """Baca file CSV dari partisi terbaru di MinIO.

    Path yang dibaca: s3a://<bucket>/<zone>/<dataset>/<partisi-terbaru>/<filename>

    Contoh:
        load_latest_partition(spark, "datalake", "raw/rdbms", "customers", "customers_from_db.csv")
    """
    base_path = f"s3a://{bucket}/{zone}/{dataset}"

    # Baca semua partisi lalu ambil yang terbaru berdasarkan nama folder (YYYY-MM-DD)
    all_partitions = spark.read.csv(f"{base_path}/*/{filename}", header=True, inferSchema=True)
    return all_partitions


def build_customer_features(
    df_customers: DataFrame,
    df_orders: DataFrame,
    df_products: DataFrame,
) -> DataFrame:
    """Bangun fitur pelanggan untuk clustering dan klasifikasi.

    Fitur yang dihasilkan:
        customer_id, age, city, total_orders, total_spend, avg_spend_per_order

    Langkah:
        1. Join orders dengan products untuk mendapatkan harga
        2. Agregasi per customer_id
        3. Join dengan tabel customers
        4. Hitung label is_high_value (1 jika total_spend >= median)
    """
    # Hitung total spend per order item
    df_order_value = df_orders.join(
        df_products.select("product_id", "price"),
        on="product_id",
        how="left",
    ).withColumn("item_value", F.col("quantity") * F.col("price"))

    # Agregasi per customer
    df_agg = df_order_value.groupBy("customer_id").agg(
        F.count("order_id").alias("total_orders"),
        F.sum("item_value").alias("total_spend"),
        F.round(F.avg("item_value"), 2).alias("avg_spend_per_order"),
    )

    # Join dengan data customer
    df_features = df_customers.select("customer_id", "customer_name", "city", "age").join(
        df_agg, on="customer_id", how="left"
    ).fillna({"total_orders": 0, "total_spend": 0.0, "avg_spend_per_order": 0.0})

    # Buat label is_high_value berdasarkan median total_spend
    median_spend = df_features.approxQuantile("total_spend", [0.5], 0.01)[0]
    df_features = df_features.withColumn(
        "is_high_value",
        F.when(F.col("total_spend") >= median_spend, 1).otherwise(0),
    )

    return df_features


def build_transaction_items(df_orders: DataFrame, df_products: DataFrame) -> DataFrame:
    """Bangun format transaksi untuk FP-Growth (association rules).

    Output: DataFrame dengan kolom (customer_id, items: list[str])

    Contoh baris:
        customer_id=1, items=["Laptop ASUS VivoBook", "Mouse Wireless Logitech", "Keyboard Mechanical Rexus"]
    """
    df_with_name = df_orders.join(
        df_products.select("product_id", "product_name"),
        on="product_id",
        how="left",
    )

    # collect_set digunakan agar tidak ada duplikat item per transaksi
    df_transactions = df_with_name.groupBy("customer_id").agg(
        F.collect_set("product_name").alias("items")
    )

    return df_transactions
