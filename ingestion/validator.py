from __future__ import annotations

import pandas as pd


def validate_dataframe(df: pd.DataFrame, source_name: str) -> list[str]:
    messages: list[str] = []

    if df.empty:
        messages.append(f"[WARNING] {source_name}: dataframe kosong.")

    duplicated = int(df.duplicated().sum())
    if duplicated > 0:
        messages.append(f"[WARNING] {source_name}: terdapat {duplicated} baris duplikat.")

    null_counts = df.isnull().sum()
    cols_with_null = [col for col, count in null_counts.items() if count > 0]
    if cols_with_null:
        messages.append(
            f"[WARNING] {source_name}: kolom dengan null -> {', '.join(cols_with_null)}"
        )

    return messages
