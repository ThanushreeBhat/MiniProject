
import pandas as pd


def read_csv_records(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Output file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    # Convert NaN values to None
    df = df.astype(object).where(
        pd.notna(df),
        None
    )

    return df.to_dict(orient="records")


def read_json_file(file_path):

    import json

    if not file_path.exists():
        raise FileNotFoundError(
            f"JSON file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
