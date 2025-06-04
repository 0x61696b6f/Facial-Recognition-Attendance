@echo off
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel --config config.yml run"
timeout /t 5
start "FastAPI App" cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 8000"