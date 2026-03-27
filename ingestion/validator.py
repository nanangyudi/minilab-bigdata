from __future__ import annotations

import pandas as pd


def validate_dataframe(
    df: pd.DataFrame,
    source_name: str,
    null_threshold: float = 0.3,
) -> tuple[list[str], bool]:
    """Validasi kualitas DataFrame.

    Returns:
        messages: daftar pesan WARNING atau ERROR.
        is_valid: False jika data ditolak (kosong atau rasio null melewati threshold).
    """
    messages: list[str] = []
    is_valid = True

    if df.empty:
        messages.append(f"[ERROR] {source_name}: dataframe kosong.")
        is_valid = False
        return messages, is_valid

    duplicated = int(df.duplicated().sum())
    if duplicated > 0:
        messages.append(f"[WARNING] {source_name}: terdapat {duplicated} baris duplikat.")

    null_counts = df.isnull().sum()
    cols_with_null = [col for col, count in null_counts.items() if count > 0]
    if cols_with_null:
        messages.append(
            f"[WARNING] {source_name}: kolom dengan null -> {', '.join(cols_with_null)}"
        )

    total_cells = len(df) * len(df.columns)
    null_ratio = df.isnull().sum().sum() / total_cells if total_cells > 0 else 0.0
    if null_ratio > null_threshold:
        messages.append(
            f"[ERROR] {source_name}: rasio null {null_ratio:.1%} melewati batas "
            f"{null_threshold:.1%} — data ditolak."
        )
        is_valid = False

    return messages, is_valid
