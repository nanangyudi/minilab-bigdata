from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import csv


LOG_PATH = Path("logs/ingestion_log.csv")


def log_event(dataset_name: str, source_type: str, rows: int, status: str, notes: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = LOG_PATH.exists()

    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "dataset_name", "source_type", "rows", "status", "notes"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), dataset_name, source_type, rows, status, notes])
