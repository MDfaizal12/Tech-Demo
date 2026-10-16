"""Streaming CSV discovery and transaction normalization."""

import csv
import os
import re
from collections.abc import Iterator
from typing import Any


REQUIRED_COLUMNS = {
    "txn_id",
    "account_id",
    "account_type",
    "amount",
    "currency",
    "description",
}
REFERENCE_TAG_PATTERN = r"#([A-Z0-9\-]+)"


def discover_csv_files(root_dir: str | os.PathLike[str]) -> list[str]:
    """Return a deterministic list of CSV files beneath ``root_dir``."""
    root = os.fspath(root_dir)
    if not os.path.isdir(root):
        if os.path.exists(root):
            raise NotADirectoryError(f"CSV search root is not a directory: {root}")
        raise FileNotFoundError(f"CSV search root does not exist: {root}")

    csv_files: list[str] = []
    for current_dir, _directories, filenames in os.walk(root):
        for filename in filenames:
            if filename.lower().endswith(".csv"):
                csv_files.append(os.path.join(current_dir, filename))
    return sorted(csv_files)


def stream_transactions(file_path: str | os.PathLike[str]) -> Iterator[dict[str, Any]]:
    """Yield validated CSV transactions one record at a time."""
    path = os.fspath(file_path)
    with open(path, mode="r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = set(reader.fieldnames or ())
        missing_columns = REQUIRED_COLUMNS - headers
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path}: missing required CSV columns: {missing}")

        for row in reader:
            line_number = reader.line_num
            if None in row:
                raise ValueError(f"{path}:{line_number}: row has extra CSV columns")
            transaction = {key: value for key, value in row.items() if key is not None}
            missing_values = [
                column
                for column in REQUIRED_COLUMNS
                if not transaction.get(column, "").strip()
            ]
            if missing_values:
                missing = ", ".join(sorted(missing_values))
                raise ValueError(
                    f"{path}:{line_number}: required transaction values are blank: "
                    f"{missing}"
                )

            description = transaction["description"].strip()
            first_tag_match = re.search(REFERENCE_TAG_PATTERN, description)
            transaction["reference_tag"] = (
                first_tag_match.group(1) if first_tag_match else None
            )
            transaction["reference_tags"] = re.findall(
                REFERENCE_TAG_PATTERN, description
            )
            transaction["clean_description"] = re.sub(
                REFERENCE_TAG_PATTERN, "", description
            ).strip()
            transaction["source_file"] = path
            transaction["source_line"] = line_number
            yield transaction
