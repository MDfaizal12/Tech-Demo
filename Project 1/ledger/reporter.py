"""CSV and visual report generation for processed ledger data."""

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def export_processed_transactions(
    processed_txns: list[dict[str, Any]], output_path: Path
) -> Path:
    """Write processed transactions to a CSV file without an index column."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(processed_txns).to_csv(output_path, index=False)
    return output_path


def generate_financial_dashboard(
    report_payload: dict[str, Any], output_path: Path
) -> Path:
    """Generate a balance and cash-flow dashboard as a PNG image."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    accounts = report_payload["accounts"]
    totals = report_payload["totals"]

    figure, (balance_axis, flow_axis) = plt.subplots(1, 2, figsize=(14, 6))

    account_ids = [account["account_id"] for account in accounts]
    balances = [account["balance_usd"] for account in accounts]
    bar_colors = ["#0072B2" if balance >= 0 else "#D55E00" for balance in balances]
    bars = balance_axis.bar(account_ids, balances, color=bar_colors)
    balance_axis.set_title("Final Account Balances")
    balance_axis.set_xlabel("Account ID")
    balance_axis.set_ylabel("Balance (USD)")
    balance_axis.yaxis.grid(True, linestyle="--", alpha=0.4)
    balance_axis.set_axisbelow(True)
    balance_axis.tick_params(axis="x", rotation=30)

    value_offset = max((abs(balance) for balance in balances), default=0.0) * 0.015
    for bar, balance in zip(bars, balances):
        label_offset = value_offset or 0.01
        vertical_alignment = "bottom" if balance >= 0 else "top"
        offset = label_offset if balance >= 0 else -label_offset
        balance_axis.text(
            bar.get_x() + bar.get_width() / 2,
            balance + offset,
            f"${balance:,.2f}",
            ha="center",
            va=vertical_alignment,
            fontsize=9,
        )

    inflows = totals["inflows_usd"]
    outflows = totals["outflows_usd"]
    flow_values = [inflows, outflows]
    flow_labels = [
        f"Total Inflows (${inflows:,.2f})",
        f"Total Outflows (${outflows:,.2f})",
    ]
    flow_axis.set_title("Inflows vs. Outflows")
    if sum(flow_values) > 0:
        flow_axis.pie(
            flow_values,
            labels=flow_labels,
            colors=["#009E73", "#D55E00"],
            autopct="%1.1f%%",
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
            textprops={"fontsize": 9},
        )
        flow_axis.axis("equal")
    else:
        flow_axis.text(
            0.5,
            0.5,
            "No inflows or outflows",
            ha="center",
            va="center",
            transform=flow_axis.transAxes,
        )
        flow_axis.set_axis_off()

    figure.tight_layout()
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return output_path
