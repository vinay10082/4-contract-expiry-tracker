"""Expiry alert evaluation."""

import sqlite3
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List

from contract_tracker.models import Contract
from contract_tracker import repository


class AlertLevel(str, Enum):
    EXPIRED = "EXPIRED"
    WARNING = "WARNING"


@dataclass
class Alert:
    contract: Contract
    level: AlertLevel
    days_until_expiry: int

    def message(self) -> str:
        c = self.contract
        if self.level is AlertLevel.EXPIRED:
            return (
                f"[EXPIRED] Contract #{c.id} '{c.name}' with {c.counterparty} "
                f"expired on {c.expiry_date.isoformat()} "
                f"({abs(self.days_until_expiry)} day(s) ago)."
            )
        return (
            f"[WARNING] Contract #{c.id} '{c.name}' with {c.counterparty} "
            f"expires on {c.expiry_date.isoformat()} "
            f"({self.days_until_expiry} day(s) remaining)."
        )


def evaluate_alerts(
    conn: sqlite3.Connection, today: date, threshold_days: int
) -> List[Alert]:
    """Return alerts for active contracts that are expired or within the warning threshold."""
    alerts: List[Alert] = []
    for contract in repository.list_contracts(conn, status="active"):
        days_remaining = contract.days_until_expiry(today)
        if days_remaining < 0:
            alerts.append(Alert(contract, AlertLevel.EXPIRED, days_remaining))
        elif days_remaining <= threshold_days:
            alerts.append(Alert(contract, AlertLevel.WARNING, days_remaining))
    alerts.sort(key=lambda a: a.days_until_expiry)
    return alerts
