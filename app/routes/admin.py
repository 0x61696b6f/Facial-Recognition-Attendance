from fastapi import APIRouter, Form, Depends, Request, File, UploadFile, Query
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.utils.auth import verify_password
from app.utils.jwt_handler import create_access_token, get_token_from_cookie, verify_token
from app.utils.location import get_location_name, get_google_maps_url
from datetime import timedelta, datetime, date
import json
import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image
from sqlalchemy import func, and_, extract
import io
import calendar
import pandas as pd

router = APIRouter()
templates = Jinja2Templates(directory="templates")

face_model = FaceAnalysis(name="antelopev2")
face_model.prepare(ctx_id=0)  

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request):
    """Helper function untuk mendapatkan user saat ini dari JWT"""
    token = get_token_from_cookie(request)
    if not token:
        return None
    try:
        username = verify_token(token)
        return username
    except:
        return None


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login_proses")
async def login_admin(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Username atau password salah"
        })
    
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,
        max_age=1800,  
        samesite="lax"
    )
    return response


@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)
    
    karyawans = db.query(models.User).all()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request, 
        "karyawans": karyawans,
        "username": username
    })


@router.get("/admin/tambah", response_class=HTMLResponse)
def form_tambah_karyawan(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("tambah_karyawan.html", {"request": request})


@router.post("/admin/tambah")
async def tambah_karyawan(
    request: Request,
    nama: str = Form(...),
    nik: str = Form(...),
    face1: UploadFile = File(None),
    face2: UploadFile = File(None),
    face3: UploadFile = File(None),
    snapshot1: str = Form(None),
    snapshot2: str = Form(None),
    snapshot3: str = Form(None),
    db: Session = Depends(get_db)
):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)

    embeddings = []
    
    
    if snapshot1 and snapshot2 and snapshot3:
        
        for i, snapshot in enumerate([snapshot1, snapshot2, snapshot3]):
            
            if "," in snapshot:
                base64_img = snapshot.split(",")[1]
            else:
                base64_img = snapshot
                
            
            import base64
            img_data = base64.b64decode(base64_img)
            img_path = f"static/temp_snapshot_{i}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data)
            
            
            img = np.array(Image.open(img_path).convert("RGB"))
            faces = face_model.get(img)
            if not faces:
                return templates.TemplateResponse("tambah_karyawan.html", {
                    "request": request,
                    "error": f"Wajah {i+1} tidak terdeteksi dalam gambar yang diambil."
                })
            emb = faces[0].embedding.tolist()
            embeddings.append(emb)
    else:
        
        if not (face1 and face2 and face3):
            return templates.TemplateResponse("tambah_karyawan.html", {
                "request": request,
                "error": "Mohon upload 3 foto wajah atau gunakan kamera untuk mengambil foto"
            })
            
        for i, file in enumerate([face1, face2, face3]):
            contents = await file.read()
            img_path = f"static/temp_face_{i}.jpg"
            with open(img_path, "wb") as f:
                f.write(contents)

            img = np.array(Image.open(img_path).convert("RGB"))
            faces = face_model.get(img)
            if not faces:
                return templates.TemplateResponse("tambah_karyawan.html", {
                    "request": request,
                    "error": f"Wajah {i+1} tidak terdeteksi."
                })
            emb = faces[0].embedding.tolist()
            embeddings.append(emb)

    
    avg_embedding = np.mean(embeddings, axis=0).tolist()
    user = models.User(nama=nama, nik=nik, face_embedding=json.dumps(avg_embedding))
    db.add(user)
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.post("/admin/hapus/{user_id}")
def hapus_karyawan(user_id: int, request: Request, db: Session = Depends(get_db)):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)
    
    try:
        
        db.query(models.Absensi).filter(models.Absensi.user_id == user_id).delete()
        
        
        user = db.query(models.User).get(user_id)
        if user:
            db.delete(user)
            db.commit()
            
        return RedirectResponse("/admin/dashboard", status_code=302)
    except Exception as e:
        db.rollback()
        return RedirectResponse("/admin/dashboard?error=Gagal menghapus karyawan", status_code=302)

@router.post("/admin/logout")
def logout_admin(request: Request):
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/admin/edit/{user_id}", response_class=HTMLResponse)
def edit_karyawan_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)
    
    karyawan = db.query(models.User).filter(models.User.id == user_id).first()
    if not karyawan:
        return RedirectResponse("/admin/dashboard", status_code=302)
    
    return templates.TemplateResponse("edit_karyawan.html", {
        "request": request, 
        "karyawan": karyawan
    })

@router.post("/admin/edit/{user_id}")
async def update_karyawan(
    user_id: int,
    request: Request,
    nama: str = Form(...),
    nik: str = Form(...),
    face1: UploadFile = File(None),
    face2: UploadFile = File(None),
    face3: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)
    
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return RedirectResponse("/admin/dashboard", status_code=302)
    
    
    user.nama = nama
    
    
    if user.nik != nik:
        existing_nik = db.query(models.User).filter(
            models.User.nik == nik, 
            models.User.id != user_id
        ).first()
        if existing_nik:
            
            return RedirectResponse(f"/admin/edit/{user_id}?error=NIK sudah digunakan", status_code=302)
        user.nik = nik
    
    
    if face1.filename and face2.filename and face3.filename:
        embeddings = []
        for i, file in enumerate([face1, face2, face3]):
            contents = await file.read()
            img_path = f"static/temp_face_{i}.jpg"
            with open(img_path, "wb") as f:
                f.write(contents)

            img = np.array(Image.open(img_path).convert("RGB"))
            faces = face_model.get(img)
            if not faces:
                return templates.TemplateResponse("edit_karyawan.html", {
                    "request": request, 
                    "karyawan": user,
                    "error": f"Wajah {i+1} tidak terdeteksi."
                })
            emb = faces[0].embedding.tolist()
            embeddings.append(emb)

        
        avg_embedding = np.mean(embeddings, axis=0).tolist()
        user.face_embedding = json.dumps(avg_embedding)
    
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/admin/laporan", response_class=HTMLResponse)
def laporan_absensi(
    request: Request, 
    tanggal: str = None, 
    db: Session = Depends(get_db)
):
    username = get_current_user(request)
    if not username:
        # Jika belum login, redirect ke halaman login
        return RedirectResponse("/login", status_code=302)
    
    
    if tanggal:
        try:
            # Parsing tanggal dari query parameter
            tanggal_obj = datetime.strptime(tanggal, "%Y-%m-%d").date()
        except ValueError:
            # Jika format tanggal salah, gunakan tanggal hari ini
            tanggal_obj = date.today()
    else:
        # Jika tidak ada parameter tanggal, gunakan tanggal hari ini
        tanggal_obj = date.today()
    
    
    tanggal_str = tanggal_obj.strftime("%d %B %Y")  # Format tanggal untuk tampilan
    
    
    karyawans = db.query(models.User).all()  # Ambil semua data karyawan
    
    
    start_of_day = datetime.combine(tanggal_obj, datetime.min.time())  # Awal hari
    end_of_day = datetime.combine(tanggal_obj, datetime.max.time())    # Akhir hari
    
    
    absensi_list = db.query(models.Absensi).filter(
        models.Absensi.timestamp >= start_of_day,
        models.Absensi.timestamp <= end_of_day
    ).all()  # Ambil absensi pada tanggal tersebut
    
    
    absensi_map = {a.user_id: a for a in absensi_list}  # Mapping user_id ke absensi
    
    
    laporan = []
    stats = {"hadir": 0, "tepat_waktu": 0, "terlambat": 0, "tidak_hadir": 0}  # Statistik absensi
    
    for karyawan in karyawans:
        if karyawan.id in absensi_map:
            absensi = absensi_map[karyawan.id]
            waktu = absensi.timestamp.strftime("%H:%M")
            status = absensi.status
            
            # Ambil lokasi absensi dan konversi ke nama lokasi dan URL Google Maps
            raw_location = absensi.lokasi
            location_data = get_location_name(raw_location)
            location_name = location_data["name"]
            coordinates = location_data["coordinates"]
            maps_url = get_google_maps_url(coordinates)
            
            stats["hadir"] += 1
            if status == "Tepat Waktu":
                stats["tepat_waktu"] += 1
            else:
                stats["terlambat"] += 1
        else:
            # Jika karyawan tidak absen hari ini
            waktu = None
            status = None
            location_name = None
            maps_url = "#"
            stats["tidak_hadir"] += 1
        
        laporan.append({
            "nama": karyawan.nama,
            "waktu": waktu,
            "status": status,
            "lokasi": location_name,
            "maps_url": maps_url
        })
    
    return templates.TemplateResponse("laporan_absensi.html", {
        "request": request,
        "tanggal": tanggal_obj.strftime("%Y-%m-%d"),
        "tanggal_str": tanggal_str,
        "laporan": laporan,
        "stats": stats
    })


@router.get("/admin/laporan/download")
def download_laporan(
    request: Request,
    tanggal: str = Query(...),
    type: str = Query(...),  
    db: Session = Depends(get_db)
):
    username = get_current_user(request)
    if not username:
        return RedirectResponse("/login", status_code=302)
    
    try:
        tanggal_obj = datetime.strptime(tanggal, "%Y-%m-%d").date()
    except ValueError:
        return RedirectResponse("/admin/laporan", status_code=302)
    
    
    karyawans = db.query(models.User).all()
    karyawan_map = {k.id: k.nama for k in karyawans}
    
    
    if type == "daily":
        
        filename = f"Laporan_Absensi_{tanggal_obj.strftime('%Y-%m-%d')}.xlsx"
        
        
        start_of_day = datetime.combine(tanggal_obj, datetime.min.time())
        end_of_day = datetime.combine(tanggal_obj, datetime.max.time())
        
        absensi_list = db.query(models.Absensi).filter(
            models.Absensi.timestamp >= start_of_day,
            models.Absensi.timestamp <= end_of_day
        ).all()
        
        
        absensi_map = {a.user_id: a for a in absensi_list}
        data = []
        
        for karyawan_id, nama in karyawan_map.items():
            if karyawan_id in absensi_map:
                absen = absensi_map[karyawan_id]
                waktu = absen.timestamp.strftime("%H:%M")
                status = absen.status
                location_data = get_location_name(absen.lokasi)
                location = location_data["name"] if location_data else "Tidak diketahui"
            else:
                waktu = "Belum Absen"
                status = "Tidak Hadir"
                location = "N/A"
            
            data.append({
                "Nama": nama,
                "Waktu Absen": waktu,
                "Status": status,
                "Lokasi": location
            })
        
    elif type == "monthly":
        
        year = tanggal_obj.year
        month = tanggal_obj.month
        month_name = tanggal_obj.strftime("%B")
        filename = f"Laporan_Bulanan_{month_name}_{year}.xlsx"
        
        
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        start_of_month = datetime.combine(start_date, datetime.min.time())
        end_of_month = datetime.combine(end_date, datetime.max.time())
        
        
        absensi_list = db.query(models.Absensi).filter(
            models.Absensi.timestamp >= start_of_month,
            models.Absensi.timestamp <= end_of_month
        ).all()
        
        
        data = []
        attendance_by_day = {}
        
        
        for day in range(1, last_day + 1):
            day_date = date(year, month, day)
            day_key = day_date.strftime("%Y-%m-%d")
            attendance_by_day[day_key] = {}
        
        
        for absen in absensi_list:
            user_id = absen.user_id
            absen_date = absen.timestamp.date()
            day_key = absen_date.strftime("%Y-%m-%d")
            
            attendance_by_day[day_key][user_id] = {
                "waktu": absen.timestamp.strftime("%H:%M"),
                "status": absen.status
            }
        
        
        for karyawan_id, nama in karyawan_map.items():
            row_data = {"Nama": nama}
            
            
            for day in range(1, last_day + 1):
                day_date = date(year, month, day)
                day_key = day_date.strftime("%Y-%m-%d")
                day_label = f"{day}"
                
                if karyawan_id in attendance_by_day[day_key]:
                    status = attendance_by_day[day_key][karyawan_id]["status"]
                    waktu = attendance_by_day[day_key][karyawan_id]["waktu"]
                    row_data[day_label] = f"{waktu} ({status})"
                else:
                    row_data[day_label] = "Tidak Hadir"
            
            data.append(row_data)
    
    else:
        return RedirectResponse("/admin/laporan", status_code=302)
    
    
    df = pd.DataFrame(data)
    
    
    output = io.BytesIO()
    
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Laporan', index=False)
        
        
        workbook = writer.book
        worksheet = writer.sheets['Laporan']
        
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D9EAD3',
            'border': 1
        })
        
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
    
    
    output.seek(0)
    
    
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')