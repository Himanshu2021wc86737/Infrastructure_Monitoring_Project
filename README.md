# Intelligent Linux Infrastructure Monitoring & Predictive Alerting System

## 1. Project purpose
A web-based infrastructure management prototype for centralized monitoring of Linux servers. It collects CPU, RAM, disk, load and uptime metrics, stores historical measurements, evaluates health status and creates threshold-based alerts.

## 2. Features
- Central web dashboard
- Local Linux metric collection
- Remote agent ingestion API
- CPU, RAM, disk and load monitoring
- Health score
- Healthy/Warning/Critical classification
- Alert history
- SQLite storage
- Demo simulator for multiple servers
- 30-second lightweight remote agent
- REST API

## 3. Installation
Linux/Windows/macOS:
```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
# venv\Scripts\activate

pip install -r requirements.txt
python run.py
```

Open: http://127.0.0.1:5000

## 4. Demo with multiple servers
Keep Flask running in one terminal. In another:
```bash
python scripts/simulate_servers.py
```
Refresh dashboard. It will show 10 sample LAB servers.

## 5. Real Linux server agent
On a monitored Linux server:
```bash
pip install psutil requests
export API_URL="http://CENTRAL_SERVER_IP:5000/api/ingest"
export ENVIRONMENT="PRODUCTION"
python scripts/linux_agent.py
```

For production, use systemd and a reverse proxy (Nginx) and add authentication/TLS before exposing the ingestion API.

## 6. Project structure
- `app/monitor.py` - Linux metrics collection and health logic
- `app/routes.py` - REST API and dashboard routes
- `app/db.py` - SQLite schema/database
- `app/templates/` - HTML
- `app/static/` - CSS/JavaScript
- `scripts/linux_agent.py` - remote monitoring agent
- `scripts/simulate_servers.py` - demo data generator
- `docs/` - project documentation

## 7. Academic scope
This prototype can be extended with PostgreSQL, authentication, email/Teams alerts, URL/port checks, anomaly detection, disk-capacity forecasting and Ansible deployment.

## 8. Security note
Do not expose `/api/ingest` to the public Internet without authentication, TLS and network controls.
