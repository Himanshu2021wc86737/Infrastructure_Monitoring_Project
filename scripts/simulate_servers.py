"""Generate sample remote server metrics continuously for demo/testing."""
import random
import time
import requests

URL = "http://127.0.0.1:5000/api/ingest"

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
            response = requests.post(URL, json=data, timeout=3)
            print(data["name"], response.status_code, response.json())
        except Exception as e:
            print(data["name"], "ERROR:", e)

    print("All 10 demo servers updated. Waiting 30 seconds...")
    time.sleep(30)