from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine


def extract_from_postgres(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
) -> pd.DataFrame:
    conn_str = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    engine = create_engine(conn_str)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df
