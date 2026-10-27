from datetime import datetime, timezone
from flask import Blueprint, jsonify, render_template, request
from .db import get_db
from .monitor import collect_local_metrics, evaluate_status, health_score

bp = Blueprint("main", __name__)

def now():
    return datetime.now(timezone.utc).isoformat()

def upsert_server(m):
    db = get_db()
    status = evaluate_status(m["cpu"], m["memory"], m["disk"])
    cur = db.execute("SELECT id FROM servers WHERE name=?", (m["name"],))
    row = cur.fetchone()
    if row:
        server_id = row["id"]
        db.execute("""UPDATE servers SET host=?, environment=?, last_seen=?,
                      cpu=?, memory=?, disk=?, uptime_seconds=?, status=?
                      WHERE id=?""",
                   (m["host"], m["environment"], m["timestamp"], m["cpu"],
                    m["memory"], m["disk"], m["uptime_seconds"], status, server_id))
    else:
        cur = db.execute("""INSERT INTO servers
                    (name,host,environment,last_seen,cpu,memory,disk,uptime_seconds,status)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (m["name"], m["host"], m["environment"], m["timestamp"],
                     m["cpu"], m["memory"], m["disk"], m["uptime_seconds"], status))
        server_id = cur.lastrowid
    db.execute("""INSERT INTO metrics(server_id,timestamp,cpu,memory,disk,load1)
                  VALUES(?,?,?,?,?,?)""",
               (server_id, m["timestamp"], m["cpu"], m["memory"], m["disk"], m["load1"]))
    if status in ("WARNING", "CRITICAL"):
        msg = f"Resource threshold exceeded: CPU {m['cpu']}%, RAM {m['memory']}%, Disk {m['disk']}%"
        db.execute("""INSERT INTO alerts(server_id,timestamp,severity,message)
                      VALUES(?,?,?,?)""", (server_id, m["timestamp"], status, msg))
    db.commit()
    return server_id, status

@bp.get("/")
def dashboard():
    return render_template("dashboard.html")

@bp.get("/api/servers")
def api_servers():
    db = get_db()
    rows = db.execute("SELECT * FROM servers ORDER BY name").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["health_score"] = health_score(d["cpu"], d["memory"], d["disk"])
        result.append(d)
    return jsonify(result)

@bp.get("/api/summary")
def api_summary():
    db = get_db()
    rows = db.execute("SELECT status, COUNT(*) c FROM servers GROUP BY status").fetchall()
    counts = {"HEALTHY":0, "WARNING":0, "CRITICAL":0, "UNKNOWN":0}
    for r in rows:
        counts[r["status"]] = r["c"]
    total = sum(counts.values())
    return jsonify({"total": total, **counts})

@bp.get("/api/server/<int:server_id>/history")
def api_history(server_id):
    db = get_db()
    rows = db.execute("""SELECT timestamp,cpu,memory,disk,load1 FROM metrics
                         WHERE server_id=? ORDER BY id DESC LIMIT 30""",
                      (server_id,)).fetchall()
    return jsonify([dict(r) for r in reversed(rows)])

@bp.get("/api/alerts")
def api_alerts():
    db = get_db()
    rows = db.execute("""SELECT alerts.*, servers.name server_name
                         FROM alerts LEFT JOIN servers ON servers.id=alerts.server_id
                         ORDER BY alerts.id DESC LIMIT 30""").fetchall()
    return jsonify([dict(r) for r in rows])

@bp.post("/api/collect")
def api_collect():
    m = collect_local_metrics()
    server_id, status = upsert_server(m)
    return jsonify({"ok": True, "server_id": server_id, "status": status, "metrics": m})

@bp.post("/api/ingest")
def api_ingest():
    data = request.get_json(silent=True) or {}
    required = ["name","host","cpu","memory","disk"]
    missing = [x for x in required if x not in data]
    if missing:
        return jsonify({"ok": False, "error": f"Missing fields: {', '.join(missing)}"}), 400
    data.setdefault("environment", "REMOTE")
    data.setdefault("uptime_seconds", 0)
    data.setdefault("load1", 0)
    data.setdefault("timestamp", now())
    try:
        for k in ("cpu","memory","disk","load1"):
            data[k] = float(data[k])
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "Metric values must be numeric"}), 400
    server_id, status = upsert_server(data)
    return jsonify({"ok": True, "server_id": server_id, "status": status})
