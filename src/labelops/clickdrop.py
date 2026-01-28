from __future__ import annotations

import csv
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from openpyxl import Workbook


@dataclass
class TrackingRecord:
    order_reference: str
    postcode: str
    service: str
    tracking_number: str | None
    created_at: str


def export_tracking_report(
    base_dir: Path,
    client_id: str,
    records: Iterable[TrackingRecord],
    report_date: date,
    batch_id: str | None = None,
) -> Path:
    output_dir = base_dir / "Clients" / client_id / "TRACKING_OUT"
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_id = batch_id or uuid.uuid4().hex[:8]
    filename = f"tracking_{report_date.isoformat()}_{batch_id}.csv"
    output_path = output_dir / filename

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "order_reference",
                "postcode",
                "service",
                "tracking_number",
                "created_at",
            ]
        )
        for record in records:
            tracking_value = record.tracking_number or "PENDING"
            writer.writerow(
                [
                    record.order_reference,
                    record.postcode,
                    record.service,
                    tracking_value,
                    record.created_at,
                ]
            )

    return output_path


def write_clickdrop_import_xlsx(
    output_path: Path, rows: list[list[str]]
) -> Path:
    workbook = Workbook()
    sheet = workbook.active

    for row in rows:
        sheet.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return output_path
