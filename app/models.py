from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from .database import Base

# Model untuk tabel admin (penyimpanan data admin aplikasi)
class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)  # Username admin unik
    password_hash = Column(Text, nullable=False)  # Password disimpan dalam bentuk hash

# Model untuk tabel users (penyimpanan data karyawan)
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)  # Nama karyawan
    nik = Column(String(50), unique=True)  # NIK unik
    face_embedding = Column(Text)  # Embedding wajah dalam bentuk JSON/text
    created_at = Column(DateTime, server_default=func.now())  # Tanggal pembuatan data

# Model untuk tabel absensi (penyimpanan data absensi karyawan)
class Absensi(Base):
    __tablename__ = 'absensi'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Relasi ke tabel users
    timestamp = Column(DateTime, server_default=func.now())  # Waktu absensi
    lokasi = Column(String(100))  # Lokasi absensi (koordinat atau nama)
    image_path = Column(String(255))  # Path gambar absensi (jika ada)
    status = Column(String(20))  # Status absensi (Tepat Waktu/Terlambat)
