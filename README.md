# Minilab Big Data — Tahap 1 (Perbaikan Selesai)

Paket ini menyiapkan lingkungan minilab big data lokal untuk pembelajaran **data ingestion ke MinIO** (zona `raw/`). Semua perbaikan fondasi (P1–P3) telah diimplementasikan dan siap dilanjutkan ke Tahap 2 (Spark & Data Mining).

## Komponen

| Komponen | Peran |
|----------|-------|
| **PostgreSQL** | Sumber data RDBMS — tabel `customers`, `products`, `orders` |
| **MinIO** | Object storage / data lake |
| **minio/mc** | Membuat bucket otomatis saat stack naik |
| **Skrip Python** (`ingestion/`) | Ekstraksi, validasi, standardisasi, unggah CSV ke MinIO |
| **Unit Test** (`tests/`) | Verifikasi modul `validator` dan `standardizer` |

## Prasyarat

- **Docker Desktop** (Windows/macOS) atau Docker Engine + Compose (Linux), **daemon harus berjalan** sebelum `docker compose up`.
- **Python 3.10+** untuk virtualenv lokal.
- Port **tidak digunakan proses lain** pada **5432** (PostgreSQL), **9000** (MinIO API), **9001** (MinIO Console) — atau ubah mapping di `.env`.

## Konfigurasi

### File konfigurasi

| File | Isi | Dipakai oleh |
|------|-----|--------------|
| `.env` | Kredensial & port (tidak di-commit) | Docker Compose + pipeline ingestion |
| `config/sources.yaml` | Sumber data RDBMS & file, target path MinIO | `ingestion/main_ingest.py` |
| `config/minio.yaml` | Endpoint, bucket, mode secure MinIO | `ingestion/main_ingest.py` |

> **Kredensial hanya di `.env`** — `sources.yaml` dan `minio.yaml` tidak lagi menyimpan password atau secret key. Pipeline membaca `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` langsung dari environment.

### Pertama kali / setelah clone

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Edit `.env` jika perlu mengubah password, port, atau nama bucket. Tidak perlu menyesuaikan file konfigurasi lain.

## Menjalankan Stack (Docker)

```bash
# Jalankan semua layanan
docker compose up -d

# Cek status — tunggu postgres dan minio berstatus healthy
docker compose ps
```

> Jika mereset database (misalnya setelah ubah `init.sql`), jalankan `docker compose down -v` terlebih dahulu agar volume lama terhapus dan data baru terbaca.

## Virtualenv dan Dependency

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

## Menjalankan Ingestion

Pastikan container sudah berjalan dan healthy, kemudian:

```bash
python -m ingestion.main_ingest
```

Pipeline akan memproses 4 sumber data secara berurutan:

| Sumber | Tipe | Dataset |
|--------|------|---------|
| `customers_from_db` | RDBMS | Tabel `customers` (30 baris) |
| `orders_from_db` | RDBMS | Tabel `orders` (63 baris) |
| `customers_from_csv` | CSV | `data/input/csv/customers.csv` (25 baris) |
| `products_from_xlsx` | XLSX | `data/input/xlsx/products.xlsx` (15 baris) |

Status setiap sumber: `SUCCESS` / `REJECTED` / `FAILED`.

## Menjalankan Unit Test

```bash
python -m pytest tests/ -v
```

18 test mencakup modul `validator` dan `standardizer`.

## Akses Layanan

| Layanan | Alamat (default) | Kredensial (default) |
|---------|-----------------|----------------------|
| PostgreSQL | `localhost:5432` | `minilab` / `minilab123` |
| MinIO API | `http://localhost:9000` | — |
| MinIO Console | `http://localhost:9001` | `minioadmin` / `minioadmin123` |

Nilai pastinya mengikuti `.env` Anda.

## Verifikasi Hasil

**Log eksekusi:**
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

## Struktur Output MinIO

Setiap run ingestion menyimpan ke sub-folder bertanggal agar tidak menimpa data lama:

```
datalake/
└── raw/
    ├── rdbms/
    │   ├── customers/<YYYY-MM-DD>/customers_from_db.csv
    │   └── orders/<YYYY-MM-DD>/orders_from_db.csv
    ├── csv/
    │   └── customers/<YYYY-MM-DD>/customers_from_csv.csv
    └── xlsx/
        └── products/<YYYY-MM-DD>/products_from_xlsx.csv
```

Setiap CSV menyertakan kolom tambahan `source_type` dan `ingestion_time`.

## Struktur Proyek

```
minilab-bigdata/
├── compose.yaml                  # Docker Compose
├── requirements.txt              # Dependensi Python
├── .env.example                  # Template environment variable
├── config/
│   ├── sources.yaml              # Sumber data (RDBMS & file)
│   └── minio.yaml                # Konfigurasi MinIO
├── data/
│   ├── sample_sql/init.sql       # Inisialisasi PostgreSQL
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
├── logs/
│   └── ingestion_log.csv
├── notebooks/
│   └── 01_ingestion_demo.ipynb
└── tests/
    ├── test_validator.py         # 10 unit test validator
    └── test_standardizer.py     # 8 unit test standardizer
```

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

### `KeyError` saat ingestion

Pastikan `.env` sudah ada (salin dari `.env.example`). Pipeline membaca variabel `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` dari file ini.

### Port sudah dipakai

Ubah variabel port di `.env`, lalu `docker compose down` dan `docker compose up -d`.

## Catatan

- **Tahap 2 (Spark & Data Mining)** belum dimulai. Dataset yang ada (`customers`, `products`, `orders`) sudah dirancang untuk mendukung klasifikasi, clustering, dan association rules.
- `.env` tidak di-commit (ada di `.gitignore`). Jika pernah ter-track, jalankan `git rm --cached .env`.
