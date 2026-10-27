import platform
import socket
import time
from datetime import datetime, timezone

import psutil

THRESHOLDS = {
    "warning": 80,
    "critical": 90
}

def collect_local_metrics():
    disk_path = "/"
    disk = psutil.disk_usage(disk_path)
    vm = psutil.virtual_memory()
    load1 = os_load1()

    return {
        "name": socket.gethostname(),
        "host": socket.gethostbyname(socket.gethostname()),
        "environment": "LOCAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": round(psutil.cpu_percent(interval=0.5), 2),
        "memory": round(vm.percent, 2),
        "disk": round(disk.percent, 2),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "load1": round(load1, 2),
        "platform": platform.platform()
    }

def os_load1():
    try:
        return psutil.getloadavg()[0]
    except (AttributeError, OSError):
        return 0.0

def evaluate_status(cpu, memory, disk):
    critical = max(cpu, memory, disk) >= THRESHOLDS["critical"]
    warning = max(cpu, memory, disk) >= THRESHOLDS["warning"]
    if critical:
        return "CRITICAL"
    if warning:
        return "WARNING"
    return "HEALTHY"

def health_score(cpu, memory, disk):
    score = 100 - (0.4*cpu + 0.3*memory + 0.3*disk)
    return max(0, min(100, round(score, 1)))
