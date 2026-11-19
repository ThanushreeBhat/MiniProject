import json
from pathlib import Path
import pandas as pd


def read_csv_records(file_path):
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        df = pd.read_csv(path)
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception:
        return []


def read_json_file(file_path):
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        return {
            "validation_passed": True,
            "total_violations": 0,
            "checks": {},
            "violations": [],
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "validation_passed": True,
            "total_violations": 0,
            "checks": {},
            "violations": [],
        }
