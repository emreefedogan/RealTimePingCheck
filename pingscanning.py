from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import subprocess
import threading
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import platform

app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gerekirse belirli bir alan adı ile değiştirin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Şablonlar için ayarlar
templates = Jinja2Templates(directory="templates")

# Global değişkenler
reachable_ips = []
unreachable_ips = []

async def ping(ip):
    try:
        # İşletim sistemine göre ping komutunu ayarla
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        result = await asyncio.create_subprocess_exec(
            'ping', param, '1', ip,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            return ip  # Ulaşılabilir
        else:
            return None  # Ulaşılamayan IP
    except Exception as e:
        print(f"Hata: {e}")  # Hata mesajını yazdır
        return None  # Hata durumunda da None döndür

async def ping_all(ips):
    global reachable_ips, unreachable_ips
    while True:
        tasks = [ping(ip) for ip in ips]
        results = await asyncio.gather(*tasks)
        
        # Ulaşılabilir ve ulaşılamayan IP adreslerini ayır
        reachable_ips = [ip for ip in results if ip is not None]
        unreachable_ips = [ip for ip in ips if ip not in reachable_ips]
        
        # Sonuçları güncelle
        print(f"Ulaşılabilir IP'ler: {reachable_ips}")
        print(f"Ulaşılamayan IP'ler: {unreachable_ips}")
        
        await asyncio.sleep(5)  # Her 5 saniyede bir kontrol et

def start_ping_task():
    ip_addresses = [f"192.168.58.{i}" for i in range(1, 513)]
    asyncio.run(ping_all(ip_addresses))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/results")
async def results():
    return {
        'reachable': reachable_ips,
        'unreachable': unreachable_ips
    }

if __name__ == "__main__":
    # Ping işlemini ayrı bir thread'de başlat
    ping_thread = threading.Thread(target=start_ping_task, daemon=True)
    ping_thread.start()
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
