# Minilab Big Data - Tahap 1

Paket ini disiapkan untuk assignment deployment minilab big data sampai tahap **ingestion data ke MinIO** (zona `raw/`).

## Komponen

- **PostgreSQL** — sumber data RDBMS (diinisialisasi dari `data/sample_sql/`)
- **MinIO** — object storage / data lake
- **minio/mc** — membuat bucket otomatis saat stack naik
- **Skrip Python** (`ingestion/`) — ekstraksi, validasi ringan, unggah CSV ke MinIO

## Prasyarat

- **Docker Desktop** (Windows/macOS) atau Docker Engine + Compose (Linux), **daemon harus berjalan** sebelum `docker compose up`.
- **Python 3.10+** (disarankan) untuk virtualenv lokal.
- Port **tidak digunakan proses lain** pada **5432** (PostgreSQL), **9000** (MinIO API), **9001** (MinIO Console) — atau ubah mapping di `.env` (lihat [Konflik port](#konflik-port)).

## Konfigurasi (penting agar tidak salah koneksi)

- **`.env`** — dipakai oleh `compose.yaml` (kredensial & port Postgres/MinIO, nama bucket). File ini **tidak di-commit** (lihat `.gitignore`). Template aman untuk disalin: **`.env.example`**.
- **`config/sources.yaml`** — dipakai skrip ingestion (host/port DB, path file CSV/XLSX, target path di MinIO).

**Pertama kali / setelah clone:** salin template ke `.env`, lalu sesuaikan jika perlu.

```bash
# Linux / macOS
cp .env.example .env
```

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

**Kredensial PostgreSQL dan MinIO di kedua file harus konsisten** (user, password, database, bucket, port Postgres ke host). Jika Anda mengubah `.env`, sesuaikan juga `config/sources.yaml` untuk bagian `rdbms` dan `minio`.

Path file sumber ada di `config/sources.yaml` (`files.csv_path`, `files.xlsx_path`). Pastikan file tersebut ada sebelum menjalankan ingestion, atau sesuaikan path-nya.

## Menjalankan services (Docker)

Dari root folder proyek ini:

```bash
docker compose up -d
```

Cek status (sebaiknya `postgres` dan `minio` **healthy**):

```bash
docker compose ps
```

## Virtualenv dan dependency (wajib sebelum ingestion)

Skrip membutuhkan paket di `requirements.txt`. Tanpa instalasi ini akan muncul error semacam `ModuleNotFoundError: No module named 'minio'`.

```bash
python -m venv .venv
```

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Jika aktivasi skrip diblokir kebijakan eksekusi, gunakan Python dari venv tanpa activate:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ingestion.main_ingest
```

**Linux / macOS**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Jalankan ingestion

Pastikan container sudah jalan dan **Postgres dapat diakses dari host** pada port yang sama dengan di `config/sources.yaml` (`rdbms.port`).

```bash
python -m ingestion.main_ingest
```

## Akses layanan

| Layanan | Alamat (default dari `.env`) |
|--------|-------------------------------|
| PostgreSQL | `localhost:5432` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |

Nilai pastinya (user, password, port) mengikuti `.env` Anda.

## Verifikasi hasil

1. **`logs/ingestion_log.csv`** — status per dataset (`SUCCESS` / `FAILED`) dan jumlah baris.
2. **MinIO Console** → bucket (default `datalake`) → prefix `raw/rdbms/`, `raw/csv/`, `raw/xlsx/` — berisi object CSV.
3. Jika preview di UI MinIO tidak tersedia, **unduh object** atau gunakan `mc` di container:  
   `docker compose exec mc mc cat local/<nama-bucket>/<path-object>.csv`

## Struktur output MinIO

- `raw/rdbms/...`
- `raw/csv/...`
- `raw/xlsx/...`

Setiap CSV menyertakan kolom tambahan `source_type` dan `ingestion_time` (lihat `ingestion/standardizer.py`).

## Troubleshooting

### `password authentication failed for user "minilab"` (dari skrip Python), tetapi container Postgres sehat

Sering terjadi jika **PostgreSQL terpisah di Windows** (atau layanan lain) masih **mendengarkan port 5432**, sehingga koneksi dari host ke `localhost:5432` **bukan** ke container.

- **Solusi A:** hentikan layanan PostgreSQL di OS (Services / `services.msc`) lalu jalankan ulang ingestion.
- **Solusi B:** ubah **`POSTGRES_PORT`** di `.env` (misalnya `5433`), jalankan `docker compose down` lalu `docker compose up -d`, dan samakan **`port`** di `config/sources.yaml` → `rdbms`.

Untuk memastikan kredensial di container benar:

```bash
docker compose exec -e PGPASSWORD=<password-dari-.env> postgres psql -U minilab -d minilabdb -c "SELECT 1;"
```

### `ModuleNotFoundError` (misalnya `minio`, `pandas`)

Gunakan venv yang sudah `pip install -r requirements.txt`, atau perintah `.\.venv\Scripts\python.exe -m ingestion.main_ingest` di Windows.

### Ingestion XLSX gagal (file tidak ditemukan)

Pastikan file ada di path yang tertulis di `config/sources.yaml` (`files.xlsx_path`), atau ubah path tersebut ke lokasi file Anda.

### Port sudah dipakai

Sesuaikan variabel port di `.env` untuk Postgres dan/atau MinIO, lalu `docker compose down` dan `docker compose up -d` lagi. Jangan lupa menyesuaikan `config/sources.yaml` untuk Postgres dan MinIO jika port API MinIO berubah.

## Catatan

- **Spark** dan zona `processed/` / `feature_store/` belum menjadi bagian tahap ini.
- Gunakan **`.env.example`** sebagai acuan; kerja aktual di **`.env`** (di-ignore git). Jika `.env` pernah ter-track sebelum ada `.gitignore`, hapus dari index dengan `git rm --cached .env` agar secret tidak ikut ter-push.
- Jika ada error saat praktikum, catat pesan error, penyebab, dan solusi/workaround untuk bahan laporan.
