from fastapi import APIRouter, Request, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
import numpy as np
import json
from datetime import date, datetime
from insightface.app import FaceAnalysis
import cv2
import io
from PIL import Image

router = APIRouter()

# Inisialisasi model face recognition InsightFace
face_model = FaceAnalysis(name="antelopev2")
face_model.prepare(ctx_id=0)

def get_db():
    # Dependency untuk mendapatkan session database
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def cosine_similarity(a, b):
    # Fungsi untuk menghitung cosine similarity antara dua embedding wajah
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@router.post("/absen")
async def absen(request: Request, db: Session = Depends(get_db)):
    # Endpoint absen berbasis embedding wajah (dari frontend)
    data = await request.json()
    embedding = data.get("embedding")
    lokasi = data.get("location", "Unknown")

    if not embedding:
        # Jika embedding tidak ditemukan di request
        return JSONResponse({"message": "Embedding tidak ditemukan"}, status_code=400)

    # Ambil seluruh user dari database
    users = db.query(models.User).all()
    threshold = 0.5  # Threshold kemiripan wajah
    matched_user = None
    max_sim = 0

    # Cari user dengan kemiripan embedding tertinggi di atas threshold
    for user in users:
        user_embedding = json.loads(user.face_embedding)
        sim = cosine_similarity(user_embedding, embedding)
        if sim > threshold and sim > max_sim:
            matched_user = user
            max_sim = sim

    if not matched_user:
        # Jika tidak ada user yang cocok
        return JSONResponse({"message": "Wajah tidak dikenali. Pastikan Anda sudah terdaftar dalam sistem."}, status_code=404)

    # Cek apakah user sudah absen hari ini
    today = date.today()
    sudah_absen = db.query(models.Absensi).filter(
        models.Absensi.user_id == matched_user.id,
        models.Absensi.timestamp >= today
    ).first()

    if sudah_absen:
        # Jika sudah absen, kembalikan pesan
        return JSONResponse({
            "message": f"{matched_user.nama} sudah absen hari ini pada {sudah_absen.timestamp.strftime('%H:%M:%S')}",
            "status": sudah_absen.status
        }, status_code=400)

    # Tentukan status absen (tepat waktu atau terlambat)
    now = datetime.now()
    batas_jam_masuk = datetime.combine(now.date(), datetime.strptime("08:00", "%H:%M").time())
    status = "Tepat Waktu" if now <= batas_jam_masuk else "Terlambat"

    # Simpan data absensi ke database
    absensi = models.Absensi(
        user_id=matched_user.id,
        lokasi=lokasi,
        status=status,
        image_path=""  # Tidak ada gambar pada endpoint ini
    )
    db.add(absensi)
    db.commit()

    return JSONResponse({
        "message": f"Absen berhasil untuk {matched_user.nama}",
        "status": status,
        "timestamp": now.strftime('%H:%M:%S')
    })

@router.post("/absen-image")
async def absen_image(
    image: UploadFile = File(...),
    location: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Baca file gambar yang diupload
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Konversi gambar ke array numpy dan ke format BGR untuk OpenCV
        img_array = np.array(pil_image)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Deteksi wajah dan ekstrak embedding dari gambar
        faces = face_model.get(img_array)
        
        if not faces:
            # Jika tidak ada wajah terdeteksi
            return JSONResponse({"message": "Wajah tidak terdeteksi dalam gambar"}, status_code=400)
        
        face_embedding = faces[0].embedding.tolist()
        
        # Cari user dengan kemiripan embedding tertinggi di atas threshold
        users = db.query(models.User).all()
        threshold = 0.5
        matched_user = None
        max_sim = 0

        for user in users:
            user_embedding = json.loads(user.face_embedding)
            sim = cosine_similarity(user_embedding, face_embedding)
            if sim > threshold and sim > max_sim:
                matched_user = user
                max_sim = sim

        if not matched_user:
            # Jika tidak ada user yang cocok
            return JSONResponse({"message": "Wajah tidak dikenali. Pastikan Anda sudah terdaftar dalam sistem."}, status_code=404)

        # Cek apakah user sudah absen hari ini
        today = date.today()
        sudah_absen = db.query(models.Absensi).filter(
            models.Absensi.user_id == matched_user.id,
            models.Absensi.timestamp >= today
        ).first()

        if sudah_absen:
            # Jika sudah absen, kembalikan pesan
            return JSONResponse({
                "message": f"{matched_user.nama} sudah absen hari ini pada {sudah_absen.timestamp.strftime('%H:%M:%S')}",
                "status": sudah_absen.status
            }, status_code=400)

        # Tentukan status absen (tepat waktu atau terlambat)
        now = datetime.now()
        batas_jam_masuk = datetime.combine(now.date(), datetime.strptime("08:00", "%H:%M").time())
        status = "Tepat Waktu" if now <= batas_jam_masuk else "Terlambat"

        # Simpan data absensi ke database
        absensi = models.Absensi(
            user_id=matched_user.id,
            lokasi=location,
            status=status,
            image_path=""
        )
        db.add(absensi)
        db.commit()

        return JSONResponse({
            "message": f"Absen berhasil untuk {matched_user.nama}",
            "status": status,
            "timestamp": now.strftime('%H:%M:%S'),
            "similarity": f"{max_sim:.2f}"
        })

    except Exception as e:
        # Tangani error yang terjadi saat proses absen
        return JSONResponse({"message": f"Terjadi kesalahan: {str(e)}"}, status_code=500)
