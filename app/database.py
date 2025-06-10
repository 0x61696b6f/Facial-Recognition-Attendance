import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL koneksi ke database MySQL menggunakan driver pymysql
DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost/absensi_db")

# Membuat engine SQLAlchemy untuk koneksi ke database
engine = create_engine(DB_URL)

# Membuat session factory untuk transaksi database
SessionLocal = sessionmaker(bind=engine)

# Base class untuk deklarasi model ORM
Base = declarative_base()
