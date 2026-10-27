"""Optional lightweight remote agent.
Run this script on each Linux server and point API_URL to the central server."""
import os, socket, time
from datetime import datetime, timezone
import psutil, requests

API_URL = os.getenv("API_URL", "http://CENTRAL_SERVER_IP:5000/api/ingest")
ENVIRONMENT = os.getenv("ENVIRONMENT", "PRODUCTION")

def load1():
    try: return psutil.getloadavg()[0]
    except: return 0

while True:
    disk = psutil.disk_usage("/")
    vm = psutil.virtual_memory()
    payload = {
        "name": socket.gethostname(),
        "host": socket.gethostbyname(socket.gethostname()),
        "environment": ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": psutil.cpu_percent(interval=1),
        "memory": vm.percent,
        "disk": disk.percent,
        "uptime_seconds": int(time.time()-psutil.boot_time()),
        "load1": load1()
    }
    try:
        print(requests.post(API_URL, json=payload, timeout=5).json())
    except Exception as e:
        print("Send failed:", e)
    time.sleep(30)
