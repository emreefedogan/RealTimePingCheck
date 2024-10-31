from flask import Flask, render_template, jsonify
import asyncio
import subprocess
import threading

app = Flask(__name__)

# Global değişkenler
reachable_ips = []
unreachable_ips = []

async def ping(ip):
    try:
        # Ping komutunu çalıştır
        result = await asyncio.create_subprocess_exec(
            'ping', '-c', '1', ip,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        # Ping sonucunu kontrol et
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    return jsonify({
        'reachable': reachable_ips,
        'unreachable': unreachable_ips
    })

if __name__ == "__main__":
    # Ping işlemini ayrı bir thread'de başlat
    threading.Thread(target=start_ping_task, daemon=True).start()
    app.run(debug=True)
