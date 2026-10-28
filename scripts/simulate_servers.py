"""Generate sample remote server metrics continuously for demo/testing."""
import random
import time
import requests

URL = "https://infrastructure-monitoring-project.onrender.com/api/ingest"
API_KEY = "2acdaa18d2912a402aa9e37078f350ea"

while True:
    for i in range(1, 11):
        cpu = random.uniform(10, 95)
        mem = random.uniform(20, 92)
        disk = random.uniform(30, 96)

        data = {
            "name": f"LAB-SRV-{i:02d}",
            "host": f"10.10.0.{i}",
            "environment": "LAB",
            "cpu": round(cpu, 2),
            "memory": round(mem, 2),
            "disk": round(disk, 2),
            "uptime_seconds": random.randint(10000, 500000),
            "load1": round(cpu / 40, 2)
        }

        try:
            response = requests.post(
    URL,
    json=data,
    headers={"X-API-Key": API_KEY},
    timeout=10
)
            print(data["name"], response.status_code, response.json())
        except Exception as e:
            print(data["name"], "ERROR:", e)

    print("All 10 demo servers updated. Waiting 30 seconds...")
    time.sleep(30)