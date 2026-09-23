"""Command-line interface for the Contract Expiry Tracker."""

import argparse
import logging
import sys
import time
from datetime import date, datetime

from contract_tracker import repository
from contract_tracker.alerts import evaluate_alerts
from contract_tracker.config import Config, load_config
from contract_tracker.database import get_connection, init_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("contract_tracker")


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date {value!r}, expected YYYY-MM-DD"
        ) from exc


def cmd_init(args: argparse.Namespace, config: Config) -> int:
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
    logger.info("Initialized database schema at %s", config.sqlite_db_path)
    return 0


def cmd_add(args: argparse.Namespace, config: Config) -> int:
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
        contract_id = repository.add_contract(
            conn,
            name=args.name,
            counterparty=args.counterparty,
            expiry_date=args.expiry_date,
            status=args.status,
            notes=args.notes,
        )
    logger.info("Added contract #%d '%s'", contract_id, args.name)
    return 0


def cmd_list(args: argparse.Namespace, config: Config) -> int:
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
        contracts = repository.list_contracts(conn, status=args.status)
    if not contracts:
        print("No contracts found.")
        return 0
    for c in contracts:
        print(
            f"#{c.id}\t{c.name}\t{c.counterparty}\t"
            f"expires={c.expiry_date.isoformat()}\tstatus={c.status}"
        )
    return 0


def cmd_update_status(args: argparse.Namespace, config: Config) -> int:
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
        updated = repository.update_status(conn, args.id, args.status)
    if not updated:
        logger.error("No contract found with id %d", args.id)
        return 1
    logger.info("Contract #%d status set to %s", args.id, args.status)
    return 0


def cmd_update_expiry(args: argparse.Namespace, config: Config) -> int:
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
        updated = repository.update_expiry_date(conn, args.id, args.expiry_date)
    if not updated:
        logger.error("No contract found with id %d", args.id)
        return 1
    logger.info("Contract #%d expiry date set to %s", args.id, args.expiry_date.isoformat())
    return 0


def cmd_remove(args: argparse.Namespace, config: Config) -> int:
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
        removed = repository.delete_contract(conn, args.id)
    if not removed:
        logger.error("No contract found with id %d", args.id)
        return 1
    logger.info("Removed contract #%d", args.id)
    return 0


def _run_check(config: Config) -> int:
    today = date.today()
    with get_connection(config.sqlite_db_path) as conn:
        init_schema(conn)
        expired_count = repository.mark_expired_contracts(conn, today)
        if expired_count:
            logger.info("Marked %d contract(s) as expired", expired_count)
        alerts = evaluate_alerts(conn, today, config.expiry_warning_threshold_days)
    if not alerts:
        logger.info("No contracts nearing expiry (threshold=%d days)", config.expiry_warning_threshold_days)
    for alert in alerts:
        logger.warning(alert.message())
    return len(alerts)


def cmd_check(args: argparse.Namespace, config: Config) -> int:
    _run_check(config)
    return 0


def cmd_run(args: argparse.Namespace, config: Config) -> int:
    interval = args.interval
    logger.info(
        "Starting polling daemon (interval=%ds, threshold=%d days, db=%s)",
        interval,
        config.expiry_warning_threshold_days,
        config.sqlite_db_path,
    )
    try:
        while True:
            _run_check(config)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Polling daemon stopped.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contract-expiry-tracker",
        description="Track contracts and alert on upcoming or past expirations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="Initialize the database schema.")
    p_init.set_defaults(func=cmd_init)

    p_add = subparsers.add_parser("add", help="Add a new contract.")
    p_add.add_argument("--name", required=True, help="Contract name/title.")
    p_add.add_argument("--counterparty", required=True, help="Counterparty organization.")
    p_add.add_argument(
        "--expiry-date", required=True, type=_parse_date, help="Expiry date (YYYY-MM-DD)."
    )
    p_add.add_argument(
        "--status",
        default="active",
        choices=sorted(repository.VALID_STATUSES),
        help="Initial status (default: active).",
    )
    p_add.add_argument("--notes", default=None, help="Optional free-text notes.")
    p_add.set_defaults(func=cmd_add)

    p_list = subparsers.add_parser("list", help="List contracts.")
    p_list.add_argument(
        "--status", default=None, choices=sorted(repository.VALID_STATUSES), help="Filter by status."
    )
    p_list.set_defaults(func=cmd_list)

    p_status = subparsers.add_parser("set-status", help="Update a contract's status.")
    p_status.add_argument("id", type=int, help="Contract id.")
    p_status.add_argument("status", choices=sorted(repository.VALID_STATUSES), help="New status.")
    p_status.set_defaults(func=cmd_update_status)

    p_expiry = subparsers.add_parser("set-expiry", help="Update a contract's expiry date.")
    p_expiry.add_argument("id", type=int, help="Contract id.")
    p_expiry.add_argument("expiry_date", type=_parse_date, help="New expiry date (YYYY-MM-DD).")
    p_expiry.set_defaults(func=cmd_update_expiry)

    p_remove = subparsers.add_parser("remove", help="Delete a contract.")
    p_remove.add_argument("id", type=int, help="Contract id.")
    p_remove.set_defaults(func=cmd_remove)

    p_check = subparsers.add_parser(
        "check", help="Run a single expiry check and print alerts."
    )
    p_check.set_defaults(func=cmd_check)

    p_run = subparsers.add_parser(
        "run", help="Run the polling daemon, periodically checking for expiring contracts."
    )
    p_run.add_argument(
        "--interval", type=int, default=3600, help="Polling interval in seconds (default: 3600)."
    )
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config()
    except ValueError as exc:
        parser.error(str(exc))
        return 2
    return args.func(args, config)


if __name__ == "__main__":
    sys.exit(main())
