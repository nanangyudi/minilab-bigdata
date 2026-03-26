from __future__ import annotations

from io import BytesIO
import pandas as pd
from minio import Minio


def upload_dataframe_as_csv(
    df: pd.DataFrame,
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    object_name: str,
    secure: bool = False,
) -> None:
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    data_stream = BytesIO(csv_bytes)

    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=data_stream,
        length=len(csv_bytes),
        content_type="text/csv",
    )
