"""
Unit test untuk ingestion/validator.py

Menguji semua skenario validasi:
- DataFrame kosong          → is_valid=False
- Baris duplikat            → WARNING (data tetap diterima)
- Kolom mengandung null     → WARNING (data tetap diterima)
- Rasio null > threshold    → is_valid=False (data ditolak)
- Data bersih               → is_valid=True, tanpa pesan
- Threshold kustom          → perilaku sesuai nilai threshold
"""
from __future__ import annotations

import pandas as pd
import pytest

from ingestion.validator import validate_dataframe


# ---------------------------------------------------------------------------
# DataFrame kosong
# ---------------------------------------------------------------------------

def test_dataframe_kosong_ditolak():
    df = pd.DataFrame()
    messages, is_valid = validate_dataframe(df, "test")
    assert not is_valid
    assert any("[ERROR]" in m for m in messages)


# ---------------------------------------------------------------------------
# Baris duplikat — WARNING saja, data tetap diterima
# ---------------------------------------------------------------------------

def test_deteksi_duplikat_menghasilkan_warning():
    df = pd.DataFrame({"a": [1, 1], "b": ["x", "x"]})
    messages, is_valid = validate_dataframe(df, "test")
    assert any("duplikat" in m for m in messages)


def test_duplikat_tidak_menolak_data():
    df = pd.DataFrame({"a": [1, 1], "b": ["x", "x"]})
    _, is_valid = validate_dataframe(df, "test")
    assert is_valid


# ---------------------------------------------------------------------------
# Nilai NULL — WARNING saja, data tetap diterima (jika di bawah threshold)
# ---------------------------------------------------------------------------

def test_deteksi_null_menghasilkan_warning():
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    messages, _ = validate_dataframe(df, "test")
    assert any("null" in m.lower() for m in messages)


def test_null_sedikit_tidak_menolak_data():
    # 1 null dari 4 sel = 25% — di bawah default threshold 30%
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    _, is_valid = validate_dataframe(df, "test")
    assert is_valid


# ---------------------------------------------------------------------------
# Rasio null melebihi threshold → data ditolak
# ---------------------------------------------------------------------------

def test_tolak_jika_null_melewati_threshold_default():
    # 2 null dari 4 sel = 50% — di atas threshold 30%
    df = pd.DataFrame({"a": [None, None], "b": ["x", "y"]})
    messages, is_valid = validate_dataframe(df, "test")
    assert not is_valid
    assert any("[ERROR]" in m for m in messages)


def test_tolak_jika_null_melewati_threshold_kustom():
    # 1 null dari 4 sel = 25% — di atas threshold kustom 10%
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    _, is_valid = validate_dataframe(df, "test", null_threshold=0.1)
    assert not is_valid


def test_lolos_jika_null_di_bawah_threshold_kustom():
    # 0 null — selalu lolos
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    _, is_valid = validate_dataframe(df, "test", null_threshold=0.0)
    assert is_valid


# ---------------------------------------------------------------------------
# Data bersih — lolos tanpa pesan apapun
# ---------------------------------------------------------------------------

def test_data_bersih_lolos_tanpa_pesan():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    messages, is_valid = validate_dataframe(df, "test")
    assert is_valid
    assert messages == []


# ---------------------------------------------------------------------------
# Return type — selalu tuple (list, bool)
# ---------------------------------------------------------------------------

def test_return_type_selalu_tuple():
    df = pd.DataFrame({"a": [1]})
    result = validate_dataframe(df, "test")
    assert isinstance(result, tuple)
    assert len(result) == 2
    messages, is_valid = result
    assert isinstance(messages, list)
    assert isinstance(is_valid, bool)
