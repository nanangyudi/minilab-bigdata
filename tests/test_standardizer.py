"""
Unit test untuk ingestion/standardizer.py

Menguji perilaku standardize_columns:
- Nama kolom diubah ke lowercase
- Spasi di nama kolom diganti underscore
- Kolom metadata source_type ditambahkan
- Kolom metadata ingestion_time ditambahkan (format ISO 8601)
- DataFrame asli tidak ikut berubah (immutability)
- Jumlah baris tidak berubah setelah standardisasi
"""
from __future__ import annotations

import pandas as pd
import pytest
from datetime import timezone
from dateutil.parser import parse as parse_dt

from ingestion.standardizer import standardize_columns


@pytest.fixture
def df_sample() -> pd.DataFrame:
    return pd.DataFrame({
        "Customer ID": [1, 2],
        "Customer Name": ["Andi", "Budi"],
        "City": ["Malang", "Blitar"],
    })


# ---------------------------------------------------------------------------
# Normalisasi nama kolom
# ---------------------------------------------------------------------------

def test_kolom_diubah_ke_lowercase(df_sample):
    result = standardize_columns(df_sample, "csv")
    assert all(col == col.lower() for col in result.columns)


def test_spasi_diganti_underscore(df_sample):
    result = standardize_columns(df_sample, "csv")
    assert "customer_id" in result.columns
    assert "customer_name" in result.columns
    assert "city" in result.columns


# ---------------------------------------------------------------------------
# Kolom metadata
# ---------------------------------------------------------------------------

def test_kolom_source_type_ditambahkan(df_sample):
    result = standardize_columns(df_sample, "rdbms")
    assert "source_type" in result.columns
    assert (result["source_type"] == "rdbms").all()


def test_kolom_ingestion_time_ditambahkan(df_sample):
    result = standardize_columns(df_sample, "csv")
    assert "ingestion_time" in result.columns


def test_ingestion_time_format_iso8601(df_sample):
    result = standardize_columns(df_sample, "csv")
    # Harus bisa di-parse sebagai datetime ISO 8601
    sample_time = result["ingestion_time"].iloc[0]
    parsed = parse_dt(sample_time)
    assert parsed.tzinfo is not None  # harus mengandung timezone info


# ---------------------------------------------------------------------------
# Immutability — DataFrame asli tidak berubah
# ---------------------------------------------------------------------------

def test_dataframe_asli_tidak_berubah(df_sample):
    kolom_awal = list(df_sample.columns)
    standardize_columns(df_sample, "csv")
    assert list(df_sample.columns) == kolom_awal


# ---------------------------------------------------------------------------
# Integritas data
# ---------------------------------------------------------------------------

def test_jumlah_baris_tidak_berubah(df_sample):
    result = standardize_columns(df_sample, "xlsx")
    assert len(result) == len(df_sample)


def test_nilai_data_tetap_sama(df_sample):
    result = standardize_columns(df_sample, "csv")
    assert result["customer_id"].tolist() == [1, 2]
    assert result["customer_name"].tolist() == ["Andi", "Budi"]
