from __future__ import annotations

import yaml

from ingestion.rdbms_extractor import extract_from_postgres
from ingestion.file_reader import read_csv_file, read_xlsx_file
from ingestion.validator import validate_dataframe
from ingestion.standardizer import standardize_columns
from ingestion.storage_writer import upload_dataframe_as_csv
from ingestion.logger import log_event


def load_config(path: str = "config/sources.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()

    minio_cfg = cfg["minio"]
    targets = cfg["targets"]

    # RDBMS ingestion
    try:
        rdbms_cfg = cfg["rdbms"]
        df_db = extract_from_postgres(
            host=rdbms_cfg["host"],
            port=rdbms_cfg["port"],
            database=rdbms_cfg["database"],
            username=rdbms_cfg["username"],
            password=rdbms_cfg["password"],
            query=rdbms_cfg["query"],
        )
        warnings = validate_dataframe(df_db, "rdbms_customers")
        df_db = standardize_columns(df_db, "rdbms")
        upload_dataframe_as_csv(
            df=df_db,
            endpoint=minio_cfg["endpoint"],
            access_key=minio_cfg["access_key"],
            secret_key=minio_cfg["secret_key"],
            bucket=minio_cfg["bucket"],
            object_name=targets["raw_rdbms_object"],
            secure=minio_cfg["secure"],
        )
        log_event("customers_from_db", "rdbms", len(df_db), "SUCCESS", " | ".join(warnings) if warnings else "OK")
        print("RDBMS ingestion berhasil.")
    except Exception as e:
        log_event("customers_from_db", "rdbms", 0, "FAILED", str(e))
        print(f"RDBMS ingestion gagal: {e}")

    # CSV ingestion
    try:
        df_csv = read_csv_file(cfg["files"]["csv_path"])
        warnings = validate_dataframe(df_csv, "csv_customers")
        df_csv = standardize_columns(df_csv, "csv")
        upload_dataframe_as_csv(
            df=df_csv,
            endpoint=minio_cfg["endpoint"],
            access_key=minio_cfg["access_key"],
            secret_key=minio_cfg["secret_key"],
            bucket=minio_cfg["bucket"],
            object_name=targets["raw_csv_object"],
            secure=minio_cfg["secure"],
        )
        log_event("customers_from_csv", "csv", len(df_csv), "SUCCESS", " | ".join(warnings) if warnings else "OK")
        print("CSV ingestion berhasil.")
    except Exception as e:
        log_event("customers_from_csv", "csv", 0, "FAILED", str(e))
        print(f"CSV ingestion gagal: {e}")

    # XLSX ingestion
    try:
        df_xlsx = read_xlsx_file(cfg["files"]["xlsx_path"])
        warnings = validate_dataframe(df_xlsx, "xlsx_products")
        df_xlsx = standardize_columns(df_xlsx, "xlsx")
        upload_dataframe_as_csv(
            df=df_xlsx,
            endpoint=minio_cfg["endpoint"],
            access_key=minio_cfg["access_key"],
            secret_key=minio_cfg["secret_key"],
            bucket=minio_cfg["bucket"],
            object_name=targets["raw_xlsx_object"],
            secure=minio_cfg["secure"],
        )
        log_event("products_from_xlsx", "xlsx", len(df_xlsx), "SUCCESS", " | ".join(warnings) if warnings else "OK")
        print("XLSX ingestion berhasil.")
    except Exception as e:
        log_event("products_from_xlsx", "xlsx", 0, "FAILED", str(e))
        print(f"XLSX ingestion gagal: {e}")


if __name__ == "__main__":
    main()
