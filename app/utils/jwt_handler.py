from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

# Konstanta untuk JWT
SECRET_KEY = "admin"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Membuat JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        # Jika diberikan waktu kadaluarsa khusus, gunakan itu
        expire = datetime.utcnow() + expires_delta
    else:
        # Jika tidak, gunakan default 30 menit
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})  # Tambahkan waktu kadaluarsa ke payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Encode JWT
    return encoded_jwt

def verify_token(token: str):
    """Memverifikasi JWT token"""
    try:
        # Decode token menggunakan SECRET_KEY dan ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            # Jika tidak ada username di payload, anggap token tidak valid
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        # Jika terjadi error saat decode, token dianggap tidak valid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_token_from_cookie(request):
    """Mengambil token dari cookie"""
    token = request.cookies.get("access_token")
    if not token:
        # Jika tidak ada token di cookie, kembalikan None
        return None
    return token
