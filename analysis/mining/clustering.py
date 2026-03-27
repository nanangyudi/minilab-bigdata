from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml import Pipeline


def run_kmeans(
    df: DataFrame,
    feature_cols: list[str],
    k: int = 3,
    seed: int = 42,
) -> tuple[DataFrame, KMeans]:
    """Jalankan K-Means clustering pada DataFrame.

    Args:
        df           : DataFrame dengan kolom fitur numerik
        feature_cols : kolom yang digunakan sebagai fitur
        k            : jumlah klaster
        seed         : random seed untuk reproduktifitas

    Returns:
        df_result : DataFrame asli + kolom 'cluster' (label klaster)
        model     : model KMeans yang sudah dilatih (untuk inspeksi centroid)

    Contoh penggunaan:
        df_result, model = run_kmeans(
            df_features,
            feature_cols=["age", "total_orders", "total_spend"],
            k=3,
        )
        df_result.select("customer_name", "city", "total_spend", "cluster").show()
    """
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="raw_features")
    scaler = StandardScaler(inputCol="raw_features", outputCol="features", withMean=True, withStd=True)
    kmeans = KMeans(featuresCol="features", predictionCol="cluster", k=k, seed=seed)

    pipeline = Pipeline(stages=[assembler, scaler, kmeans])
    model = pipeline.fit(df)
    df_result = model.transform(df).drop("raw_features", "features")

    return df_result, model
