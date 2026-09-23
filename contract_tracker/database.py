"""SQLite connection handling and schema management."""

import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS contracts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    counterparty    TEXT NOT NULL,
    expiry_date     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_contracts_expiry_date ON contracts (expiry_date);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts (status);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


@contextmanager
def get_connection(db_path: str):
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()
