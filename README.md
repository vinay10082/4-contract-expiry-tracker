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
Initialize the database schema, ingest contract metadata, and execute the polling daemon to emit expiry alerts.

## Testing & CI
Unit tests utilize an in-memory SQLite database (`:memory:`) to validate temporal polling logic without disk I/O.
