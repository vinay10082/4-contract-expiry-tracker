"""Data model for a tracked contract."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Contract:
    id: Optional[int]
    name: str
    counterparty: str
    expiry_date: date
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Contract":
        return cls(
            id=row["id"],
            name=row["name"],
            counterparty=row["counterparty"],
            expiry_date=date.fromisoformat(row["expiry_date"]),
            status=row["status"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def days_until_expiry(self, today: date) -> int:
        return (self.expiry_date - today).days
