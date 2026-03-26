from __future__ import annotations

import pandas as pd


def read_csv_file(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def read_xlsx_file(path: str) -> pd.DataFrame:
    return pd.read_excel(path)
