from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.routes import admin, web, absensi
from app.middleware.auth_middleware import JWTAuthMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

app = FastAPI()

# Mount folder static untuk file statis (CSS, JS, gambar, dll)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tambahkan middleware autentikasi JWT untuk proteksi route tertentu
app.add_middleware(JWTAuthMiddleware)

# Middleware untuk membatasi host yang diizinkan mengakses aplikasi
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["absensi.aiko-nextcloud.my.id", "localhost"]
)

# Middleware untuk redirect HTTP ke HTTPS jika diperlukan
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.headers.get('x-forwarded-proto') == 'http':
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url))
        return await call_next(request)

app.add_middleware(HTTPSRedirectMiddleware)

# Register semua router aplikasi (admin, web, absensi)
app.include_router(admin.router)
app.include_router(web.router)
app.include_router(absensi.router)