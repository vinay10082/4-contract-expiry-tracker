# Contract Expiry Tracker

## Description
A transactional tracking system for monitoring and alerting on contract expiration dates.

## Architecture Overview
Row-oriented embedded SQLite database coupled with a chronologically scheduled polling engine.

## Prerequisites
* Python 3.11+
* SQLite3

## Environment Variables
* `SQLITE_DB_PATH`
* `EXPIRY_WARNING_THRESHOLD_DAYS`

## Quick Start & Usage
```bash
# Optional: point at a specific database file and warning window (defaults shown)
export SQLITE_DB_PATH="./contracts.db"
export EXPIRY_WARNING_THRESHOLD_DAYS=30

# Initialize the database schema
python main.py init

# Add a contract
python main.py add --name "Vendor SLA" --counterparty "Acme Corp" --expiry-date 2026-10-15

# List contracts (optionally filter by status: active, expired, renewed, cancelled)
python main.py list
python main.py list --status active

# Update a contract's status or expiry date
python main.py set-status 1 renewed
python main.py set-expiry 1 2027-10-15

# Remove a contract
python main.py remove 1

# Run a single expiry check (auto-marks past-due contracts as expired, prints alerts)
python main.py check

# Run the polling daemon, checking on an interval (seconds)
python main.py run --interval 3600
```

## Architecture
* `contract_tracker/config.py` — loads `SQLITE_DB_PATH` / `EXPIRY_WARNING_THRESHOLD_DAYS` from the environment.
* `contract_tracker/database.py` — SQLite connection handling and schema management.
* `contract_tracker/models.py` — `Contract` data model.
* `contract_tracker/repository.py` — CRUD operations against the `contracts` table.
* `contract_tracker/alerts.py` — evaluates active contracts against the warning threshold and produces alerts.
* `contract_tracker/cli.py` — argparse-based CLI wiring the above together.
* `main.py` — entry point.
