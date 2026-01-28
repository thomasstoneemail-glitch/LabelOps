from pathlib import Path

from openpyxl import load_workbook

from labelops.clickdrop import write_clickdrop_import_xlsx


def test_clickdrop_import_has_no_header_row(tmp_path: Path) -> None:
    output_path = tmp_path / "import.xlsx"
    rows = [
        ["ORDER-1", "Recipient", "Address 1"],
        ["ORDER-2", "Recipient", "Address 2"],
    ]

    write_clickdrop_import_xlsx(output_path, rows)

    workbook = load_workbook(output_path)
    sheet = workbook.active
    first_row = [cell.value for cell in sheet[1]]

    assert first_row == rows[0]
    assert first_row != ["order_reference", "name", "address"]
