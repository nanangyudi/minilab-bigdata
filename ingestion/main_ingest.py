from __future__ import annotations

import os
from datetime import date
from typing import Callable

import yaml
from dotenv import load_dotenv

from ingestion.rdbms_extractor import extract_from_postgres
from ingestion.file_reader import read_csv_file, read_xlsx_file
from ingestion.validator import validate_dataframe
from ingestion.standardizer import standardize_columns
from ingestion.storage_writer import upload_dataframe_as_csv
from ingestion.logger import log_event


def load_config(
    sources_path: str = "config/sources.yaml",
    minio_path: str = "config/minio.yaml",
) -> tuple[dict, dict]:
    with open(sources_path, "r", encoding="utf-8") as f:
        sources = yaml.safe_load(f)
    with open(minio_path, "r", encoding="utf-8") as f:
        minio = yaml.safe_load(f)
    return sources, minio


def add_partition(object_name: str) -> str:
    """Sisipkan partisi tanggal sebelum nama file.

    Contoh:
        raw/rdbms/customers/customers_from_db.csv
        -> raw/rdbms/customers/2026-03-27/customers_from_db.csv
    """
    partition = date.today().isoformat()
    base, filename = object_name.rsplit("/", 1)
    return f"{base}/{partition}/{filename}"


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
            object_name=add_partition(object_name),
            secure=minio_cfg["secure"],
        )
        log_event(name, source_type, len(df), "SUCCESS", " | ".join(warnings) if warnings else "OK")
        print(f"[OK] {name}: ingestion berhasil ({len(df)} baris).")

    except Exception as e:
        log_event(name, source_type, 0, "FAILED", str(e))
        print(f"[ERROR] {name}: ingestion gagal — {e}")


def main() -> None:
    load_dotenv()
    cfg, minio_raw = load_config()

    minio_cfg = {
        "endpoint": minio_raw["endpoint"],
        "access_key": os.environ["MINIO_ROOT_USER"],
        "secret_key": os.environ["MINIO_ROOT_PASSWORD"],
        "bucket": minio_raw["bucket"],
        "secure": minio_raw["secure"],
    }

    rdbms_cfg = cfg["rdbms"]
    for src in rdbms_cfg["sources"]:
        run_ingestion(
            name=src["name"],
            source_type="rdbms",
            extract_fn=lambda q=src["query"]: extract_from_postgres(
                host=rdbms_cfg["host"],
                port=rdbms_cfg["port"],
                database=rdbms_cfg["database"],
                username=rdbms_cfg["username"],
                password=os.environ["POSTGRES_PASSWORD"],
                query=q,
            ),
            object_name=src["target"],
            minio_cfg=minio_cfg,
        )

    readers = {"csv": read_csv_file, "xlsx": read_xlsx_file}
    for src in cfg["files"]:
        run_ingestion(
            name=src["name"],
            source_type=src["source_type"],
            extract_fn=lambda p=src["path"], t=src["source_type"]: readers[t](p),
            object_name=src["target"],
            minio_cfg=minio_cfg,
        )


if __name__ == "__main__":
    main()
