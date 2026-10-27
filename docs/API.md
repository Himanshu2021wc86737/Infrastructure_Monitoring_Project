# API Reference

GET `/api/summary`
Returns server counts by status.

GET `/api/servers`
Returns server inventory and health score.

GET `/api/server/<id>/history`
Returns recent metric history.

GET `/api/alerts`
Returns recent alerts.

POST `/api/collect`
Collects metrics from the machine running the Flask server.

POST `/api/ingest`
Accepts remote agent JSON:
```json
{
  "name":"APP01",
  "host":"10.0.0.10",
  "environment":"PRODUCTION",
  "cpu":72,
  "memory":64,
  "disk":81,
  "uptime_seconds":123456,
  "load1":1.2
}
```
