#!/usr/bin/env python3
"""
Generator dataset besar untuk simulasi pemrosesan terdistribusi (Tahap 3).
Menghasilkan 10.000 pelanggan, 100 produk, 1.000.000 order dengan pola
asosiasi yang disengaja — lalu mengunggah ke MinIO zona raw/large/.

Cara pakai:
    python -m data.generate_large_dataset
    python -m data.generate_large_dataset --orders 500000
"""
from __future__ import annotations

import argparse
import io
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from minio import Minio

load_dotenv()

# ── Konfigurasi ──────────────────────────────────────────────────────────────
N_CUSTOMERS = 10_000
N_PRODUCTS  = 100
N_ORDERS    = 1_000_000
SEED        = 42

CITIES = [
    "Jakarta", "Surabaya", "Bandung", "Medan", "Makassar",
    "Semarang", "Palembang", "Depok", "Tangerang", "Bekasi",
]

# 10 kategori × 10 produk = 100 produk
CATALOG: dict[str, list[str]] = {
    "Elektronik":  ["Laptop", "Mouse", "Keyboard", "Monitor", "Webcam",
                    "Headphone", "Smartphone", "Tablet", "Printer", "Speaker"],
    "Fashion":     ["Jaket", "Celana", "Kemeja", "Kaos", "Sepatu",
                    "Topi", "Tas", "Dompet", "Ikat Pinggang", "Kacamata"],
    "Makanan":     ["Kopi", "Teh", "Gula", "Minyak Goreng", "Beras",
                    "Mie Instan", "Kecap", "Saus", "Susu", "Coklat"],
    "Olahraga":    ["Sepatu Lari", "Bola", "Raket", "Matras Yoga", "Dumbbell",
                    "Jersey", "Pelindung Lutut", "Tas Olahraga", "Topi Olahraga", "Kaos Kaki"],
    "Dapur":       ["Panci", "Blender", "Wajan", "Pisau Dapur", "Talenan",
                    "Rice Cooker", "Kompor", "Kulkas Mini", "Toaster", "Thermos"],
    "Kecantikan":  ["Sabun", "Shampo", "Kondisioner", "Pelembab", "Sunscreen",
                    "Lipstik", "Maskara", "Foundation", "Parfum", "Deodoran"],
    "Otomotif":    ["Helm", "Sarung Tangan Motor", "Cover Motor", "Oli Motor", "Ban Motor",
                    "Lampu Motor", "Kunci Cadangan", "Jas Hujan", "Kaca Spion", "Klakson"],
    "Buku":        ["Novel", "Komik", "Buku Pelajaran", "Majalah", "Buku Resep",
                    "Buku Motivasi", "Kamus", "Atlas", "Buku Gambar", "Planner"],
    "Kesehatan":   ["Vitamin C", "Masker", "Hand Sanitizer", "Obat Flu", "Termometer",
                    "Tensimeter", "Bandage", "Antiseptik", "Probiotik", "Suplemen"],
    "Rumah":       ["Bantal", "Selimut", "Gorden", "Karpet", "Lampu LED",
                    "Cermin", "Rak Dinding", "Tempat Sampah", "Sapu", "Taplak Meja"],
}

# Pola asosiasi yang disengaja: (produk pemicu, produk ikutan, probabilitas)
ASSOC_PATTERNS: list[tuple[str, list[str], float]] = [
    ("Laptop",        ["Mouse", "Keyboard"],                  0.65),
    ("Smartphone",    ["Headphone", "Speaker"],               0.55),
    ("Kopi",          ["Teh", "Gula"],                        0.60),
    ("Jaket",         ["Celana"],                             0.55),
    ("Sepatu Lari",   ["Kaos Kaki", "Bola"],                  0.50),
    ("Panci",         ["Blender", "Wajan"],                   0.50),
    ("Sabun",         ["Shampo", "Kondisioner"],              0.60),
    ("Helm",          ["Sarung Tangan Motor", "Jas Hujan"],   0.55),
]


# ── Generator ─────────────────────────────────────────────────────────────────

def build_products() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    pid = 1
    for category, names in CATALOG.items():
        for name in names:
            price = int(rng.integers(5_000, 2_000_001))
            stock = int(rng.integers(10, 501))
            rows.append((pid, name, category, price, stock))
            pid += 1
    return pd.DataFrame(rows, columns=["product_id", "name", "category", "price", "stock"])


def build_customers() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    first = ["Adi","Budi","Citra","Dewi","Eko","Fani","Gilang","Hana","Irfan","Julia",
             "Krisna","Linda","Mario","Nina","Oscar","Putri","Qadir","Rina","Sandi","Tina"]
    last  = ["Santoso","Wijaya","Kusuma","Pratama","Hidayat","Sari","Rahman","Utama",
             "Putra","Dewi","Susanto","Wibowo","Hartono","Nugroho","Setiawan"]
    rng2 = np.random.default_rng(SEED + 1)
    names = [
        f"{first[i % len(first)]} {last[i % len(last)]} {i // (len(first)*len(last)) + 1}"
        if i >= len(first) * len(last)
        else f"{first[i % len(first)]} {last[i % len(last)]}"
        for i in range(N_CUSTOMERS)
    ]
    cities     = rng.choice(CITIES, size=N_CUSTOMERS)
    ages       = rng.integers(18, 61, size=N_CUSTOMERS)
    base_date  = date(2022, 1, 1)
    signups    = [str(base_date + timedelta(days=int(d))) for d in rng.integers(0, 730, size=N_CUSTOMERS)]
    return pd.DataFrame({
        "customer_id": range(1, N_CUSTOMERS + 1),
        "name":        names,
        "city":        cities,
        "age":         ages,
        "signup_date": signups,
    })


def build_orders(df_products: pd.DataFrame, n_orders: int) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    # Indeks produk berdasarkan nama untuk pola asosiasi
    name_to_id = dict(zip(df_products["name"], df_products["product_id"]))
    trigger_ids  = {name_to_id[t]: ([name_to_id[a] for a in assoc if a in name_to_id], prob)
                    for t, assoc, prob in ASSOC_PATTERNS if t in name_to_id}

    customer_ids = rng.integers(1, N_CUSTOMERS + 1, size=n_orders)
    product_ids  = rng.integers(1, N_PRODUCTS + 1,  size=n_orders)
    quantities   = rng.integers(1, 6,                size=n_orders)
    base_date    = date(2023, 1, 1)
    order_dates  = [str(base_date + timedelta(days=int(d))) for d in rng.integers(0, 730, size=n_orders)]

    rows = list(zip(
        range(1, n_orders + 1),
        customer_ids.tolist(),
        product_ids.tolist(),
        quantities.tolist(),
        order_dates,
    ))

    # Sisipkan baris asosiasi
    extra: list[tuple] = []
    next_id = n_orders + 1
    prob_roll = rng.random(size=n_orders)

    for i, (oid, cid, pid, qty, odate) in enumerate(rows):
        if pid in trigger_ids:
            assoc_ids, prob = trigger_ids[pid]
            if prob_roll[i] < prob:
                for apid in assoc_ids:
                    extra.append((next_id, cid, apid, int(rng.integers(1, 4)), odate))
                    next_id += 1

    all_rows = rows + extra
    return pd.DataFrame(all_rows, columns=["order_id", "customer_id", "product_id", "quantity", "order_date"])


# ── Upload ke MinIO ────────────────────────────────────────────────────────────

def _minio_client() -> tuple[Minio, str]:
    endpoint   = os.environ.get("MINIO_ENDPOINT", "localhost:9000").replace("http://", "").replace("https://", "")
    access_key = os.environ["MINIO_ROOT_USER"]
    secret_key = os.environ["MINIO_ROOT_PASSWORD"]
    bucket     = os.environ.get("MINIO_BUCKET", "datalake")
    client     = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    return client, bucket


def _upload(client: Minio, bucket: str, path: str, df: pd.DataFrame) -> None:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    client.put_object(bucket, path, io.BytesIO(csv_bytes), len(csv_bytes), content_type="text/csv")
    print(f"  ✓ {path}  ({len(df):,} baris, {len(csv_bytes)/1_048_576:.1f} MB)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main(n_orders: int = N_ORDERS) -> None:
    print("=== Generate Large Dataset ===")
    print(f"  Pelanggan : {N_CUSTOMERS:,}")
    print(f"  Produk    : {N_PRODUCTS}")
    print(f"  Order     : {n_orders:,} (+ baris asosiasi)")
    print()

    print("Membuat data...")
    df_products  = build_products()
    df_customers = build_customers()
    df_orders    = build_orders(df_products, n_orders)

    print(f"  Total order setelah sisipan asosiasi: {len(df_orders):,}")
    print()

    print("Mengunggah ke MinIO (raw/large/)...")
    client, bucket = _minio_client()
    _upload(client, bucket, "raw/large/customers/customers_large.csv", df_customers)
    _upload(client, bucket, "raw/large/products/products_large.csv",   df_products)
    _upload(client, bucket, "raw/large/orders/orders_large.csv",       df_orders)

    print()
    print("Selesai. Jalankan notebook 06 atau 07 untuk analisis.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate large synthetic dataset")
    parser.add_argument("--orders", type=int, default=N_ORDERS,
                        help=f"Jumlah order dasar (default: {N_ORDERS:,})")
    args = parser.parse_args()
    main(n_orders=args.orders)
