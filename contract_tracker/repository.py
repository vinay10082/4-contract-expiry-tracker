"""CRUD operations against the contracts table."""

import sqlite3
from datetime import date
from typing import List, Optional

from contract_tracker.models import Contract

VALID_STATUSES = {"active", "expired", "renewed", "cancelled"}


def add_contract(
    conn: sqlite3.Connection,
    name: str,
    counterparty: str,
    expiry_date: date,
    status: str = "active",
    notes: Optional[str] = None,
) -> int:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}, got {status!r}")
    cursor = conn.execute(
        """
        INSERT INTO contracts (name, counterparty, expiry_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, counterparty, expiry_date.isoformat(), status, notes),
    )
    conn.commit()
    return cursor.lastrowid


def get_contract(conn: sqlite3.Connection, contract_id: int) -> Optional[Contract]:
    row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    return Contract.from_row(row) if row else None


def list_contracts(
    conn: sqlite3.Connection, status: Optional[str] = None
) -> List[Contract]:
    if status:
        rows = conn.execute(
            "SELECT * FROM contracts WHERE status = ? ORDER BY expiry_date ASC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM contracts ORDER BY expiry_date ASC").fetchall()
    return [Contract.from_row(row) for row in rows]


def list_expiring_within(
    conn: sqlite3.Connection, today: date, threshold_days: int
) -> List[Contract]:
    horizon = today.fromordinal(today.toordinal() + threshold_days)
    rows = conn.execute(
        """
        SELECT * FROM contracts
        WHERE status = 'active' AND expiry_date <= ?
        ORDER BY expiry_date ASC
        """,
        (horizon.isoformat(),),
    ).fetchall()
    return [Contract.from_row(row) for row in rows]


def update_status(conn: sqlite3.Connection, contract_id: int, status: str) -> bool:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}, got {status!r}")
    cursor = conn.execute(
        "UPDATE contracts SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, contract_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def update_expiry_date(conn: sqlite3.Connection, contract_id: int, expiry_date: date) -> bool:
    cursor = conn.execute(
        "UPDATE contracts SET expiry_date = ?, updated_at = datetime('now') WHERE id = ?",
        (expiry_date.isoformat(), contract_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def delete_contract(conn: sqlite3.Connection, contract_id: int) -> bool:
    cursor = conn.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
    conn.commit()
    return cursor.rowcount > 0


def mark_expired_contracts(conn: sqlite3.Connection, today: date) -> int:
    cursor = conn.execute(
        """
        UPDATE contracts SET status = 'expired', updated_at = datetime('now')
        WHERE status = 'active' AND expiry_date < ?
        """,
        (today.isoformat(),),
    )
    conn.commit()
    return cursor.rowcount
