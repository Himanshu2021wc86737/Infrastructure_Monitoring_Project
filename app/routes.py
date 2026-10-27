
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template, request

from .db import get_db
from .monitor import (
    collect_local_metrics,
    evaluate_status,
    health_score,
)

bp = Blueprint("main", __name__)


def now():
    return datetime.now(timezone.utc).isoformat()


def upsert_server(m):
    db = get_db()

    status = evaluate_status(
        m["cpu"],
        m["memory"],
        m["disk"],
    )

    cur = db.execute(
        "SELECT id FROM servers WHERE name=?",
        (m["name"],),
    )
    row = cur.fetchone()

    if row:
        server_id = row["id"]

        db.execute(
            """
            UPDATE servers
            SET host=?, environment=?, last_seen=?,
                cpu=?, memory=?, disk=?,
                uptime_seconds=?, status=?
            WHERE id=?
            """,
            (
                m["host"],
                m["environment"],
                m["timestamp"],
                m["cpu"],
                m["memory"],
                m["disk"],
                m["uptime_seconds"],
                status,
                server_id,
            ),
        )
    else:
        cur = db.execute(
            """
            INSERT INTO servers
            (name, host, environment, last_seen,
             cpu, memory, disk, uptime_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                m["name"],
                m["host"],
                m["environment"],
                m["timestamp"],
                m["cpu"],
                m["memory"],
                m["disk"],
                m["uptime_seconds"],
                status,
            ),
        )
        server_id = cur.lastrowid

    db.execute(
        """
        INSERT INTO metrics
        (server_id, timestamp, cpu, memory, disk, load1)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            server_id,
            m["timestamp"],
            m["cpu"],
            m["memory"],
            m["disk"],
            m["load1"],
        ),
    )

    if status in ("WARNING", "CRITICAL"):
        msg = (
            f"Resource threshold exceeded: "
            f"CPU {m['cpu']}%, RAM {m['memory']}%, "
            f"Disk {m['disk']}%"
        )

        db.execute(
            """
            INSERT INTO alerts
            (server_id, timestamp, severity, message)
            VALUES (?, ?, ?, ?)
            """,
            (server_id, m["timestamp"], status, msg),
        )

    db.commit()
    return server_id, status


@bp.get("/")
def dashboard():
    return render_template("dashboard.html")


@bp.get("/api/servers")
def api_servers():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM servers WHERE environment = 'LAB' ORDER BY name"
    ).fetchall()

    result = []

    for row in rows:
        server = dict(row)
        server["health_score"] = health_score(
            server["cpu"],
            server["memory"],
            server["disk"],
        )
        result.append(server)

    return jsonify(result)


@bp.get("/api/summary")
def api_summary():
    db = get_db()

    rows = db.execute(
        "SELECT status, COUNT(*) c FROM servers WHERE environment = 'LAB' GROUP BY status"
    ).fetchall()

    counts = {
        "HEALTHY": 0,
        "WARNING": 0,
        "CRITICAL": 0,
        "UNKNOWN": 0,
    }

    for row in rows:
        counts[row["status"]] = row["c"]

    return jsonify({
        "total": sum(counts.values()),
        **counts,
    })


@bp.get("/api/server/<int:server_id>/history")
def api_history(server_id):
    db = get_db()

    rows = db.execute(
        """
        SELECT timestamp, cpu, memory, disk, load1
        FROM metrics
        WHERE server_id=?
        ORDER BY id DESC
        LIMIT 30
        """,
        (server_id,),
    ).fetchall()

    return jsonify([
        dict(row) for row in reversed(rows)
    ])


@bp.get("/api/alerts")
def api_alerts():
    db = get_db()

    rows = db.execute(
        """SELECT alerts.*, servers.name server_name
   FROM alerts
   JOIN servers ON servers.id = alerts.server_id
   WHERE servers.environment = 'LAB'
   ORDER BY alerts.id DESC LIMIT 30"""
    ).fetchall()

    return jsonify([dict(row) for row in rows])


@bp.post("/api/collect")
def api_collect():
    metrics = collect_local_metrics()
    server_id, status = upsert_server(metrics)

    return jsonify({
        "ok": True,
        "server_id": server_id,
        "status": status,
        "metrics": metrics,
    })


@bp.post("/api/ingest")
def api_ingest():
    # Require an API key for incoming server metrics.
    expected_key = os.environ.get("INGEST_API_KEY")
    provided_key = request.headers.get("X-API-Key")

    if not expected_key or provided_key != expected_key:
        return jsonify({
            "ok": False,
            "error": "Unauthorized",
        }), 401

    data = request.get_json(silent=True) or {}

    required = ["name", "host", "cpu", "memory", "disk"]
    missing = [
        field for field in required
        if field not in data
    ]

    if missing:
        return jsonify({
            "ok": False,
            "error": f"Missing fields: {', '.join(missing)}",
        }), 400

    data.setdefault("environment", "REMOTE")
    data.setdefault("uptime_seconds", 0)
    data.setdefault("load1", 0)
    data.setdefault("timestamp", now())

    try:
        for field in ("cpu", "memory", "disk", "load1"):
            data[field] = float(data[field])

            if not (
                float("-inf") < data[field] < float("inf")
            ):
                raise ValueError("Metric must be finite")

        for field in ("cpu", "memory", "disk"):
            if not 0 <= data[field] <= 100:
                return jsonify({
                    "ok": False,
                    "error": f"{field} must be between 0 and 100",
                }), 400

        if data["uptime_seconds"] < 0:
            return jsonify({
                "ok": False,
                "error": "uptime_seconds cannot be negative",
            }), 400

    except (ValueError, TypeError, OverflowError):
        return jsonify({
            "ok": False,
            "error": "Metric values must be valid numbers",
        }), 400

    server_id, status = upsert_server(data)

    return jsonify({
        "ok": True,
        "server_id": server_id,
        "status": status,
    })