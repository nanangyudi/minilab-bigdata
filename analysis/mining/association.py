from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.ml.fpm import FPGrowth


def run_fpgrowth(
    df_transactions: DataFrame,
    items_col: str = "items",
    min_support: float = 0.1,
    min_confidence: float = 0.5,
) -> tuple[DataFrame, DataFrame]:
    """Jalankan FP-Growth untuk menemukan association rules.

    Args:
        df_transactions : DataFrame dengan kolom berisi list item per transaksi
        items_col       : nama kolom yang berisi list item (default: "items")
        min_support     : minimum support (proporsi transaksi yang memuat itemset)
        min_confidence  : minimum confidence untuk membentuk rule

    Returns:
        df_freq_items : frequent itemsets beserta support count
        df_rules      : association rules (antecedent → consequent, confidence, lift)

    Contoh penggunaan:
        df_freq, df_rules = run_fpgrowth(df_transactions, min_support=0.1, min_confidence=0.5)
        df_rules.orderBy("lift", ascending=False).show(truncate=False)

    Interpretasi kolom rules:
        antecedent  : produk yang dibeli (IF)
        consequent  : produk yang cenderung ikut dibeli (THEN)
        confidence  : P(consequent | antecedent)
        lift        : seberapa jauh lebih sering dibanding kebetulan (>1 = positif)
    """
    fpgrowth = FPGrowth(
        itemsCol=items_col,
        minSupport=min_support,
        minConfidence=min_confidence,
    )
    model = fpgrowth.fit(df_transactions)

    df_freq_items = model.freqItemsets
    df_rules = model.associationRules

    return df_freq_items, df_rules
