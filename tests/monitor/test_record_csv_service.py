import csv
import re
from pathlib import Path

from monitor.services.record_csv_service import COLUMNS, RecordCsvService


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def test_append_writes_header_once_and_one_row_per_record(
    tmp_path: Path, sample_record: dict
) -> None:
    service = RecordCsvService(csv_dir=tmp_path / "tabular")

    service.append(dict(sample_record, Usage_kWh=3.5))
    service.append(dict(sample_record, Usage_kWh=4.5))

    header, rows = _read_csv(tmp_path / "tabular" / "records_history.csv")
    assert header == COLUMNS
    assert [row["Usage_kWh"] for row in rows] == ["3.5", "4.5"]
    assert rows[0]["Load_Type"] == "Light_Load"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", rows[0]["received_at"])


def test_append_ignores_unknown_keys_and_blanks_missing_ones(tmp_path: Path) -> None:
    service = RecordCsvService(csv_dir=tmp_path)

    service.append({"date": "24/09/2026 10:15:03", "unknown": "x"})

    header, rows = _read_csv(tmp_path / "records_history.csv")
    assert "unknown" not in header
    assert rows[0]["date"] == "24/09/2026 10:15:03"
    assert rows[0]["Usage_kWh"] == ""


def test_append_does_not_mutate_the_input(tmp_path: Path, sample_record: dict) -> None:
    original = dict(sample_record)

    RecordCsvService(csv_dir=tmp_path).append(sample_record)

    assert sample_record == original
