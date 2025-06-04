from app.database import Base, engine
from app import models

print("Membuat tabel-tabel di database...")
Base.metadata.create_all(bind=engine)
print("Selesai.")
