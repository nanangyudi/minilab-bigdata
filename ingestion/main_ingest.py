from __future__ import annotations

import os
from typing import Callable

import yaml
from dotenv import load_dotenv

from ingestion.rdbms_extractor import extract_from_postgres
from ingestion.file_reader import read_csv_file, read_xlsx_file
from ingestion.validator import validate_dataframe
from ingestion.standardizer import standardize_columns
from ingestion.storage_writer import upload_dataframe_as_csv
from ingestion.logger import log_event


def load_config(path: str = "config/sources.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_ingestion(
    name: str,
    source_type: str,
    extract_fn: Callable,
    object_name: str,
    minio_cfg: dict,
) -> None:
    """Jalankan satu siklus ingestion: extract → validate → standardize → upload → log."""
    try:
        df = extract_fn()
        warnings, is_valid = validate_dataframe(df, name)

        if not is_valid:
            log_event(name, source_type, 0, "REJECTED", " | ".join(warnings))
            print(f"[REJECTED] {name}: data ditolak karena tidak memenuhi threshold kualitas.")
            return

        df = standardize_columns(df, source_type)
        upload_dataframe_as_csv(
            df=df,
            endpoint=minio_cfg["endpoint"],
            access_key=minio_cfg["access_key"],
            secret_key=minio_cfg["secret_key"],
            bucket=minio_cfg["bucket"],
            object_name=object_name,
            secure=minio_cfg["secure"],
        )
        log_event(name, source_type, len(df), "SUCCESS", " | ".join(warnings) if warnings else "OK")
        print(f"[OK] {name}: ingestion berhasil ({len(df)} baris).")

    except Exception as e:
        log_event(name, source_type, 0, "FAILED", str(e))
        print(f"[ERROR] {name}: ingestion gagal — {e}")


def main() -> None:
    load_dotenv()
    cfg = load_config()

    minio_cfg = {
        "endpoint": cfg["minio"]["endpoint"],
        "access_key": os.environ["MINIO_ROOT_USER"],
        "secret_key": os.environ["MINIO_ROOT_PASSWORD"],
        "bucket": cfg["minio"]["bucket"],
        "secure": cfg["minio"]["secure"],
    }
    targets = cfg["targets"]
    rdbms_cfg = cfg["rdbms"]

    run_ingestion(
        name="customers_from_db",
        source_type="rdbms",
        extract_fn=lambda: extract_from_postgres(
            host=rdbms_cfg["host"],
            port=rdbms_cfg["port"],
            database=rdbms_cfg["database"],
            username=rdbms_cfg["username"],
            password=os.environ["POSTGRES_PASSWORD"],
            query=rdbms_cfg["query"],
        ),
        object_name=targets["raw_rdbms_object"],
        minio_cfg=minio_cfg,
    )

    run_ingestion(
        name="customers_from_csv",
        source_type="csv",
        extract_fn=lambda: read_csv_file(cfg["files"]["csv_path"]),
        object_name=targets["raw_csv_object"],
        minio_cfg=minio_cfg,
    )

    run_ingestion(
        name="products_from_xlsx",
        source_type="xlsx",
        extract_fn=lambda: read_xlsx_file(cfg["files"]["xlsx_path"]),
        object_name=targets["raw_xlsx_object"],
        minio_cfg=minio_cfg,
    )


if __name__ == "__main__":
    main()
