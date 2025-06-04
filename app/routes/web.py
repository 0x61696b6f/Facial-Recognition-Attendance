from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def absensi_page(request: Request):
    return templates.TemplateResponse("absensi.html", {"request": request})