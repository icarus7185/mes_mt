"""Archives predicted tabular records into a CSV file for permanent history."""

import csv
from datetime import datetime
from pathlib import Path

COLUMNS = [
    "received_at",
    "date",
    "Usage_kWh",
    "Lagging_Current_Reactive.Power_kVarh",
    "Leading_Current_Reactive_Power_kVarh",
    "CO2(tCO2)",
    "Lagging_Current_Power_Factor",
    "Leading_Current_Power_Factor",
    "NSM",
    "WeekStatus",
    "Day_of_week",
    "Load_Type",
]


class RecordCsvService:
    """Appends each predicted record as a new row to a single CSV file."""

    def __init__(self, csv_dir: Path, filename: str = "records_history.csv") -> None:
        self.csv_path = csv_dir / filename

    def append(self, record: dict) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        is_new_file = not self.csv_path.exists()

        row = dict(record)
        row["received_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.csv_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
            if is_new_file:
                writer.writeheader()
            writer.writerow(row)
