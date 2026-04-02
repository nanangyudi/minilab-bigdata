# Minilab Big Data & Analitik

Proyek minilab untuk pembelajaran **Big Data dan Analitik** — mencakup dua tahap penuh:

| Tahap | Topik | Status |
|-------|-------|--------|
| **Tahap 1** | Data Ingestion ke MinIO (zona `raw/`) | ✅ Selesai |
| **Tahap 2** | Analisis Data dengan Spark & Data Mining | ✅ Selesai |

---

## Komponen

| Komponen | Peran |
|----------|-------|
| **PostgreSQL** | Sumber data RDBMS — tabel `customers`, `products`, `orders` |
| **MinIO** | Object storage / data lake (zona `raw/` dan `processed/`) |
| **minio/mc** | Membuat bucket otomatis saat stack naik |
| **Skrip Python** (`ingestion/`) | Ekstraksi, validasi, standardisasi, unggah CSV ke MinIO |
| **Modul PySpark** (`analysis/`) | Feature engineering, K-Means, Decision Tree, FP-Growth |
| **JupyterLab** | Antarmuka notebook untuk eksplorasi & analisis |
| **Unit Test** (`tests/`) | Verifikasi modul `validator` dan `standardizer` |

---

## Prasyarat

- **Docker Desktop** (Windows/macOS) atau Docker Engine + Compose (Linux), **daemon harus berjalan** sebelum `docker compose up`.
- **Python 3.10+** untuk virtualenv lokal (Tahap 1).
- Port **tidak digunakan proses lain** pada **5432** (PostgreSQL), **9000** (MinIO API), **9001** (MinIO Console), **8888** (JupyterLab) — atau ubah mapping di `.env`.

---

## Konfigurasi

### File konfigurasi

| File | Isi | Dipakai oleh |
|------|-----|--------------|
| `.env` | Kredensial & port (tidak di-commit) | Docker Compose + pipeline |
| `config/sources.yaml` | Sumber data RDBMS & file, target path MinIO | `ingestion/main_ingest.py` |
| `config/minio.yaml` | Endpoint, bucket, mode secure MinIO | `ingestion/main_ingest.py` |

> **Kredensial hanya di `.env`** — `sources.yaml` dan `minio.yaml` tidak menyimpan password atau secret key. Pipeline membaca `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` langsung dari environment.

### Pertama kali / setelah clone

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Edit `.env` jika perlu mengubah password, port, atau nama bucket.

---

## Menjalankan Stack (Docker)

### Tahap 1 saja (PostgreSQL + MinIO)

```bash
docker compose up -d
docker compose ps   # tunggu postgres dan minio berstatus healthy
```

### Tahap 1 + Tahap 2 (+ JupyterLab/PySpark)

```bash
docker compose --profile analysis up -d
```

| Service | Profile | Image | Port |
|---------|---------|-------|------|
| postgres | *(selalu)* | postgres:16 | 5432 |
| minio | *(selalu)* | minio/minio | 9000, 9001 |
| mc | *(selalu)* | minio/mc | — |
| **jupyter** | **analysis** | **jupyter/pyspark-notebook** | **8888** |

> Untuk mereset database (misalnya setelah ubah `init.sql`), jalankan `docker compose down -v` terlebih dahulu.

---

## Virtualenv dan Dependency (Tahap 1)

```bash
python -m venv .venv
```

**Windows (PowerShell)**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Jika aktivasi skrip diblokir kebijakan eksekusi:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ingestion.main_ingest
```

**Linux / macOS**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Menjalankan Ingestion (Tahap 1)

Pastikan container sudah berjalan dan healthy, kemudian:

```bash
python -m ingestion.main_ingest
```

Pipeline memproses 4 sumber data secara berurutan:

| Sumber | Tipe | Dataset |
|--------|------|---------|
| `customers_from_db` | RDBMS | Tabel `customers` (30 baris) |
| `orders_from_db` | RDBMS | Tabel `orders` (63 baris) |
| `customers_from_csv` | CSV | `data/input/csv/customers.csv` (25 baris) |
| `products_from_xlsx` | XLSX | `data/input/xlsx/products.xlsx` (15 baris) |

Status setiap sumber: `SUCCESS` / `REJECTED` / `FAILED`.

---

## Menjalankan Unit Test

```bash
python -m pytest tests/ -v
```

18 test mencakup modul `validator` dan `standardizer`.

---

## Menjalankan Analisis (Tahap 2)

### 1. Pastikan data sudah ada di MinIO

```bash
python -m ingestion.main_ingest
```

### 2. Jalankan JupyterLab

```bash
docker compose --profile analysis up -d
```

### 3. Dapatkan token akses

```bash
# Linux / macOS
docker logs minilab-jupyter 2>&1 | grep token

# Windows (PowerShell)
docker logs minilab-jupyter 2>&1 | Select-String "token"
```

Salin URL yang mengandung `token=...` dan buka di browser: `http://localhost:8888`

### 4. Urutan notebook

```
work/notebooks/
├── 02_eda_spark.ipynb           → EDA + simpan processed/customer_features/
├── 03_clustering.ipynb          → K-Means segmentasi pelanggan
├── 04_classification.ipynb      → Decision Tree prediksi is_high_value
└── 05_association_rules.ipynb   → FP-Growth pola pembelian
```

> Notebook 02 harus dijalankan terlebih dahulu karena notebook 03 dan 04 membaca output-nya dari `processed/customer_features/`.

---

## Akses Layanan

| Layanan | Alamat (default) | Kredensial (default) |
|---------|-----------------|----------------------|
| PostgreSQL | `localhost:5432` | `minilab` / `minilab123` |
| MinIO API | `http://localhost:9000` | — |
| MinIO Console | `http://localhost:9001` | `minioadmin` / `minioadmin123` |
| JupyterLab | `http://localhost:8888` | token dari log container |

Nilai pastinya mengikuti `.env` Anda.

---

## Verifikasi Hasil

**Log eksekusi ingestion:**
```bash
cat logs/ingestion_log.csv
```

**Cek isi MinIO via terminal:**
```bash
# List semua objek
docker exec minilab-mc mc ls local/datalake --recursive

# Lihat isi file
docker exec minilab-mc mc cat local/datalake/raw/rdbms/customers/<tanggal>/customers_from_db.csv
```

**MinIO Console:** buka `http://localhost:9001` → bucket `datalake`.

---

## Struktur Output MinIO

```
datalake/
├── raw/                                  ← Tahap 1 (ingestion)
│   ├── rdbms/
│   │   ├── customers/<YYYY-MM-DD>/customers_from_db.csv
│   │   └── orders/<YYYY-MM-DD>/orders_from_db.csv
│   ├── csv/
│   │   └── customers/<YYYY-MM-DD>/customers_from_csv.csv
│   └── xlsx/
│       └── products/<YYYY-MM-DD>/products_from_xlsx.csv
└── processed/                            ← Tahap 2 (analisis)
    ├── customer_features/                ← output notebook 02
    ├── customer_clusters/                ← output notebook 03
    ├── classification_results/           ← output notebook 04
    └── association_rules/                ← output notebook 05
```

Setiap CSV raw menyertakan kolom tambahan `source_type` dan `ingestion_time`.

---

## Struktur Proyek

```
minilab-bigdata/
├── compose.yaml                  # Docker Compose (profile: analysis untuk Jupyter)
├── requirements.txt              # Dependensi Python Tahap 1
├── analysis-requirements.txt     # Dependensi tambahan container Jupyter
├── .env.example                  # Template environment variable
├── config/
│   ├── sources.yaml              # Sumber data (RDBMS & file)
│   └── minio.yaml                # Konfigurasi MinIO
├── data/
│   ├── sample_sql/init.sql       # Inisialisasi PostgreSQL (30 customers, 15 products, 63 orders)
│   └── input/
│       ├── csv/customers.csv
│       └── xlsx/products.xlsx
├── ingestion/
│   ├── main_ingest.py            # Orkestrasi pipeline
│   ├── rdbms_extractor.py        # Ekstraksi PostgreSQL
│   ├── file_reader.py            # Baca CSV / XLSX
│   ├── validator.py              # Validasi kualitas data
│   ├── standardizer.py           # Normalisasi kolom + metadata
│   ├── storage_writer.py         # Upload ke MinIO
│   └── logger.py                 # Log eksekusi
├── analysis/
│   ├── spark_session.py          # SparkSession + konfigurasi S3A ke MinIO
│   ├── preprocessing.py          # Load data dari MinIO + feature engineering
│   └── mining/
│       ├── clustering.py         # K-Means (Spark MLlib)
│       ├── classification.py     # Decision Tree + evaluasi AUC
│       └── association.py        # FP-Growth association rules
├── notebooks/
│   ├── 01_ingestion_demo.ipynb   # Demo ingestion pipeline
│   ├── 02_eda_spark.ipynb        # EDA dengan Spark
│   ├── 03_clustering.ipynb       # K-Means clustering
│   ├── 04_classification.ipynb   # Decision Tree classification
│   └── 05_association_rules.ipynb # FP-Growth association rules
├── logs/
│   └── ingestion_log.csv
└── tests/
    ├── test_validator.py         # 10 unit test validator
    └── test_standardizer.py      # 8 unit test standardizer
```

---

## Troubleshooting

### `password authentication failed for user "minilab"`

Biasanya karena PostgreSQL di OS host masih mendengarkan port 5432.

- **Solusi A:** hentikan layanan PostgreSQL di OS → jalankan ulang ingestion.
- **Solusi B:** ubah `POSTGRES_PORT` di `.env` (misal `5433`) → `docker compose down` → `docker compose up -d`.

Verifikasi kredensial di container:
```bash
docker compose exec -e PGPASSWORD=<password> postgres psql -U minilab -d minilabdb -c "SELECT 1;"
```

### `ModuleNotFoundError`

Aktifkan virtualenv dan pastikan sudah `pip install -r requirements.txt`.

### `ClassNotFoundException: S3AFileSystem` (di JupyterLab)

JAR hadoop-aws diunduh otomatis saat SparkSession pertama kali dibuat (butuh koneksi internet). Tunggu hingga proses selesai.

### `KeyError` saat ingestion

Pastikan `.env` sudah ada (salin dari `.env.example`). Pipeline membaca variabel `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` dari file ini.

### Port sudah dipakai

Ubah variabel port di `.env`, lalu `docker compose down` dan `docker compose up -d`.

### Notebook tidak bisa dibuka (NotJSONError)

Biasanya karena conflict marker dari `git merge`. Ambil versi bersih dari server:
```bash
git checkout origin/<branch> -- notebooks/<nama_notebook>.ipynb
```
