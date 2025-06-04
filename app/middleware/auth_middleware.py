from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.jwt_handler import verify_token, get_token_from_cookie

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
        # Daftar route yang membutuhkan autentikasi JWT
        self.protected_routes = [
            "/admin/dashboard",
            "/admin/tambah",
            "/admin/hapus",
            "/admin/laporan"
        ]
        
        # Daftar route yang bersifat publik (tidak perlu autentikasi)
        self.public_routes = [
            "/login",
            "/login_proses",
            "/absensi",
            "/absen",
            "/absen-image"
        ]

    async def dispatch(self, request: Request, call_next):
        # Ambil path dari request yang masuk
        path = str(request.url.path)
        
        # Cek apakah path termasuk route yang dilindungi (perlu autentikasi)
        needs_auth = any(path.startswith(route) for route in self.protected_routes)
        
        if needs_auth:
            # Ambil token dari cookie
            token = get_token_from_cookie(request)
            if not token:
                # Jika tidak ada token, redirect ke halaman login
                return RedirectResponse(url="/login", status_code=302)
            
            try:
                # Verifikasi token JWT
                username = verify_token(token)
                # Simpan username user yang sedang login ke state request
                request.state.current_user = username
            except HTTPException:
                # Jika token tidak valid, hapus cookie dan redirect ke login
                response = RedirectResponse(url="/login", status_code=302)
                response.delete_cookie("access_token")
                return response
        
        # Lanjutkan ke proses berikutnya (route handler)
        response = await call_next(request)
        return response
