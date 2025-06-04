# Sistem Absensi Face Recognition

Sistem Absensi ini merupakan aplikasi berbasis web yang memanfaatkan teknologi **Face Recognition** untuk melakukan absensi karyawan secara otomatis dan akurat. Sistem ini dilengkapi dengan fitur dashboard admin, laporan absensi harian dan bulanan, serta pengelolaan data karyawan.

## Fitur Utama

- **Absensi Otomatis**: Karyawan dapat melakukan absensi dengan memindai wajah menggunakan kamera perangkat.
- **Face Recognition**: Menggunakan model InsightFace untuk mengenali wajah karyawan.
- **Lokasi Absensi**: Lokasi absensi dicatat menggunakan koordinat GPS dan dapat dilihat di Google Maps.
- **Dashboard Admin**: Admin dapat mengelola data karyawan, melihat dan mengunduh laporan absensi.
- **Laporan Absensi**: Laporan harian dan bulanan dapat diunduh dalam format Excel.
- **Keamanan**: Login admin menggunakan autentikasi JWT.

## Teknologi yang Digunakan

- **Backend**: FastAPI (Python)
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Face Recognition**: InsightFace, OpenCV, Pillow, Numpy
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Template Engine**: Jinja2
- **Cloudflare Tunnel**: Untuk akses publik via internet

## Instalasi & Setup

### 1. Clone Repository

```bash
git clone https://github.com/0x61696b6f/Facial-Recognition-Attendance
cd Meme
```

### 2. Install Python & MySQL

- Pastikan Python 3.8+ sudah terinstall.
- Install dan jalankan MySQL, buat database dengan nama `absensi_db`.

### 3. Install Dependencies

Gunakan pip untuk menginstall semua dependensi:

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Database

Pastikan file `app/database.py` sudah sesuai dengan konfigurasi MySQL Anda:

```python
DB_URL = "mysql+pymysql://root:@localhost/absensi_db"
```
Ubah `root` dan password jika diperlukan.

### 5. Inisialisasi Database

Jalankan script berikut untuk membuat tabel di database:

```bash
python init_db.py
```

### 6. Buat Admin Pertama

Generate hash password admin:

```bash
python init_admin.py
```
Salin hash yang dihasilkan, lalu masukkan ke tabel `admin` di database MySQL secara manual, misal via phpMyAdmin atau MySQL CLI:

```sql
INSERT INTO admin (username, password_hash) VALUES ('admin', '<hash_dari_init_admin.py>');
```

### 7. Jalankan Aplikasi

Gunakan batch file yang sudah disediakan:

```bash
start_app.bat
```

Atau jalankan manual:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8. (Opsional) Jalankan Cloudflare Tunnel

Agar aplikasi dapat diakses publik, gunakan Cloudflare Tunnel, buat dan konfigurasikan file `config.yml`:
```yml
tunnel: TUNNEL_ID
credentials-file: CREDENTIAL_FILE_PATH.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

---

## Penggunaan

- **Halaman Absensi**: Akses melalui root URL (`/`). Karyawan dapat absen dengan kamera.
- **Login Admin**: Akses `/login` untuk masuk sebagai admin.
- **Dashboard Admin**: Kelola karyawan, lihat dan unduh laporan absensi.

---

## Catatan

- Pastikan perangkat memiliki kamera untuk fitur absensi wajah.
- Untuk pengenalan wajah yang akurat, gunakan foto wajah yang jelas saat menambah karyawan.
- Jika ingin mengganti model face recognition, sesuaikan pada bagian inisialisasi `FaceAnalysis` di kode.

---

## Lisensi

Proyek ini dibuat untuk keperluan pembelajaran dan tugas akhir. Silakan gunakan dan modifikasi sesuai kebutuhan.

