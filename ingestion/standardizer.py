from __future__ import annotations

import pandas as pd
from datetime import datetime, timezone


def standardize_columns(df: pd.DataFrame, source_type: str) -> pd.DataFrame:
    clean_df = df.copy()
    clean_df.columns = [
        str(col).strip().lower().replace(" ", "_") for col in clean_df.columns
    ]
    clean_df["source_type"] = source_type
    clean_df["ingestion_time"] = datetime.now(timezone.utc).isoformat()
    return clean_df
