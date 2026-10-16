"""Orchestrate CSV ingestion, account posting, and summary persistence."""

from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
import secrets
from typing import Any

from ledger import (
    BaseAccount,
    CorporateAccount,
    CurrencyConverter,
    SavingsAccount,
)
from ledger.parser import discover_csv_files, stream_transactions
from ledger.reporter import (
    export_processed_transactions,
    generate_financial_dashboard,
)


LOGGER = logging.getLogger(__name__)
ACCOUNT_TYPES = {
    "savings": SavingsAccount,
    "corporate": CorporateAccount,
}


def _account_definitions(csv_files: list[str]) -> dict[str, str]:
    """Discover account IDs and enforce a consistent type across all files."""
    account_types: dict[str, str] = {}
    for file_path in csv_files:
        for transaction in stream_transactions(file_path):
            account_id = transaction["account_id"].strip()
            account_type = transaction["account_type"].strip().lower()
            if account_type not in ACCOUNT_TYPES:
                raise ValueError(
                    f"{file_path}:{transaction['source_line']}: unsupported "
                    f"account_type {account_type!r}"
                )
            previous_type = account_types.setdefault(account_id, account_type)
            if previous_type != account_type:
                raise ValueError(
                    f"Account {account_id!r} has conflicting types: "
                    f"{previous_type!r} and {account_type!r}"
                )
    return account_types


def bootstrap_accounts(account_types: dict[str, str]) -> dict[str, BaseAccount]:
    """Create zero-opening-balance accounts and private runtime credentials."""
    accounts: dict[str, BaseAccount] = {}
    for account_id, account_type in sorted(account_types.items()):
        account_class = ACCOUNT_TYPES[account_type]
        accounts[account_id] = account_class(
            account_id=account_id,
            auth_token=secrets.token_urlsafe(32),
        )
    return accounts


def _format_currency(amount: float) -> str:
    """Format a USD amount with a currency symbol and thousands separators."""
    return f"${amount:,.2f} USD"


def _print_summary(payload: dict[str, Any], report_path: Path, base_dir: Path) -> None:
    """Print a concise, aligned terminal summary of the generated report."""
    totals = payload["totals"]
    print(f"Inflows:        {_format_currency(totals['inflows_usd'])}")
    print(f"Outflows:       {_format_currency(totals['outflows_usd'])}")
    print(f"Net cash flow:  {_format_currency(totals['net_cash_flow_usd'])}")

    print("\nAccount balances:")
    for account in payload["accounts"]:
        balance = f"${account['balance_usd']:,.2f}"
        line = f"  {account['account_id']}: {balance:>10}"
        if account["statement_fees_usd"]:
            line += (
                f" USD (statement fee: "
                f"{_format_currency(account['statement_fees_usd'])[:-4]})"
            )
        else:
            line += " USD"
        print(line)

    print("\nTop 3 expenses:")
    for expense in payload["top_3_expenses"]:
        formatted_amount = f"${expense['amount_usd']:,.2f}"
        print(
            f"  {expense['txn_id']:<10} "
            f"{formatted_amount:>10}  {expense['description']}"
        )

    print(f"\nReport saved to: {os.path.relpath(report_path, base_dir)}")


def run_pipeline(project_dir: Path | None = None) -> dict[str, Any]:
    """Process all raw CSVs, write a JSON report, and return its payload."""
    base_dir = project_dir or Path(__file__).resolve().parent
    raw_data_dir = base_dir / "data" / "raw"
    reports_dir = base_dir / "data" / "reports"
    os.makedirs(reports_dir, exist_ok=True)

    csv_files = discover_csv_files(raw_data_dir)
    if not csv_files:
        raise FileNotFoundError(f"No CSV transaction files found in {raw_data_dir}")

    account_types = _account_definitions(csv_files)
    accounts = bootstrap_accounts(account_types)
    converter = CurrencyConverter()
    posted_transactions: list[dict[str, Any]] = []

    for file_path in csv_files:
        for transaction in stream_transactions(file_path):
            try:
                amount = float(transaction["amount"])
            except ValueError as exc:
                raise ValueError(
                    f"{file_path}:{transaction['source_line']}: invalid amount "
                    f"{transaction['amount']!r}"
                ) from exc
            if not math.isfinite(amount):
                raise ValueError(
                    f"{file_path}:{transaction['source_line']}: amount must be finite"
                )

            currency = transaction["currency"].strip().upper()
            base_amount = converter.convert_to_base(amount, currency)
            account = accounts[transaction["account_id"]]
            account.post_transaction(amount, base_amount)
            posted_transactions.append(
                {
                    "txn_id": transaction["txn_id"].strip(),
                    "account_id": transaction["account_id"].strip(),
                    "account_type": transaction["account_type"].strip().lower(),
                    "amount": round(amount, 2),
                    "currency": currency,
                    "base_amount_usd": base_amount,
                    "description": transaction["clean_description"],
                    "reference_tag": transaction["reference_tag"],
                    "reference_tags": transaction["reference_tags"],
                    "source_file": os.path.relpath(file_path, base_dir),
                    "source_line": transaction["source_line"],
                }
            )

    inflows = sum(
        transaction["base_amount_usd"]
        for transaction in posted_transactions
        if transaction["base_amount_usd"] > 0
    )
    outflows = sum(
        abs(transaction["base_amount_usd"])
        for transaction in posted_transactions
        if transaction["base_amount_usd"] < 0
    )
    top_expenses = sorted(
        (
            transaction
            for transaction in posted_transactions
            if transaction["base_amount_usd"] < 0
        ),
        key=lambda transaction: (
            abs(transaction["base_amount_usd"]),
            transaction["txn_id"],
        ),
        reverse=True,
    )[:3]

    account_summaries = [
        {
            "account_id": account_id,
            "account_type": account_types[account_id],
            "balance_usd": round(account.balance, 2),
            "statement_fees_usd": round(account.calculate_statement_fees(), 2),
        }
        for account_id, account in sorted(accounts.items())
    ]
    payload = {
        "report_title": "Project 3: Automated Financial Ledger & Currency Converter",
        "base_currency": "USD",
        "transaction_count": len(posted_transactions),
        "source_files": [
            os.path.relpath(file_path, base_dir) for file_path in csv_files
        ],
        "totals": {
            "inflows_usd": round(inflows, 2),
            "outflows_usd": round(outflows, 2),
            "net_cash_flow_usd": round(inflows - outflows, 2),
        },
        "accounts": account_summaries,
        "top_3_expenses": [
            {
                "txn_id": transaction["txn_id"],
                "account_id": transaction["account_id"],
                "amount_usd": round(abs(transaction["base_amount_usd"]), 2),
                "description": transaction["description"],
                "reference_tags": transaction["reference_tags"],
            }
            for transaction in top_expenses
        ],
        "transactions": posted_transactions,
    }

    csv_path = export_processed_transactions(
        posted_transactions, reports_dir / "processed_transactions.csv"
    )
    dashboard_path = generate_financial_dashboard(
        payload, reports_dir / "financial_dashboard.png"
    )
    print(
        "Processed transactions CSV saved to: "
        f"{os.path.relpath(csv_path, base_dir)}"
    )
    print(
        "Financial dashboard saved to: "
        f"{os.path.relpath(dashboard_path, base_dir)}"
    )

    report_path = reports_dir / "financial_summary.json"
    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(payload, report_file, indent=2, ensure_ascii=False)
        report_file.write("\n")

    LOGGER.info("Wrote financial report to %s", report_path)
    _print_summary(payload, report_path, base_dir)
    return payload


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run_pipeline()
