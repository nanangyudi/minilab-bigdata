from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml import Pipeline


def run_decision_tree(
    df: DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str],
    label_col: str = "is_high_value",
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[DataFrame, float]:
    """Latih Decision Tree classifier dan evaluasi pada test set.

    Args:
        df               : DataFrame fitur + label
        numeric_cols     : kolom numerik (langsung dipakai sebagai fitur)
        categorical_cols : kolom kategorik (di-index oleh StringIndexer)
        label_col        : nama kolom label (default: is_high_value)
        test_ratio       : proporsi data untuk test (default: 20%)
        seed             : random seed

    Returns:
        df_predictions : test set + kolom 'prediction' dan 'probability'
        auc            : Area Under ROC Curve pada test set

    Contoh penggunaan:
        df_pred, auc = run_decision_tree(
            df_features,
            numeric_cols=["age", "total_orders", "total_spend"],
            categorical_cols=["city"],
        )
        print(f"AUC: {auc:.3f}")
        df_pred.select("customer_name", "is_high_value", "prediction").show()
    """
    train_df, test_df = df.randomSplit([1 - test_ratio, test_ratio], seed=seed)

    # Encode kolom kategorik
    indexers = [
        StringIndexer(inputCol=col, outputCol=f"{col}_idx", handleInvalid="keep")
        for col in categorical_cols
    ]
    indexed_cols = numeric_cols + [f"{col}_idx" for col in categorical_cols]

    assembler = VectorAssembler(inputCols=indexed_cols, outputCol="features")
    dt = DecisionTreeClassifier(
        featuresCol="features",
        labelCol=label_col,
        predictionCol="prediction",
        maxDepth=5,
    )

    pipeline = Pipeline(stages=indexers + [assembler, dt])
    model = pipeline.fit(train_df)
    df_predictions = model.transform(test_df).drop("features")

    evaluator = BinaryClassificationEvaluator(labelCol=label_col, metricName="areaUnderROC")
    auc = evaluator.evaluate(df_predictions)

    return df_predictions, auc
