import sqlite3
from pathlib import Path
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    host TEXT NOT NULL,
    environment TEXT NOT NULL DEFAULT 'LAB',
    last_seen TEXT,
    cpu REAL DEFAULT 0,
    memory REAL DEFAULT 0,
    disk REAL DEFAULT 0,
    uptime_seconds INTEGER DEFAULT 0,
    status TEXT DEFAULT 'UNKNOWN'
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    cpu REAL,
    memory REAL,
    disk REAL,
    load1 REAL,
    FOREIGN KEY(server_id) REFERENCES servers(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    FOREIGN KEY(server_id) REFERENCES servers(id)
);
"""

def get_db():
    if "db" not in g:
        db_path = Path(current_app.root_path).parent / current_app.config["DATABASE"]
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()
