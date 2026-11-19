
import pandas as pd

from backend.config import (
    TASK_FILE,
    BLOCK_FILE,
    TRAIN_FILE,
    ASSET_FEATURE_FILE,
    ASSET_MASTER_FILE,
    MAINTENANCE_HISTORY_FILE,
    RISK_TRAINING_FILE,
    create_directories,
)


def check_file(file_path):
    """Check whether a required file exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )


def check_columns(dataframe, required_columns, file_name):
    """Check whether required columns exist."""

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"{file_name} is missing columns: "
            f"{sorted(missing)}"
        )


def load_core_data():
    """
    Load the three main railway scheduling datasets.

    These files are stored in data/raw/.
    """

    check_file(TASK_FILE)
    check_file(BLOCK_FILE)
    check_file(TRAIN_FILE)

    tasks = pd.read_csv(TASK_FILE)
    blocks = pd.read_csv(BLOCK_FILE)
    trains = pd.read_csv(TRAIN_FILE)

    # Validate maintenance task columns
    check_columns(
        tasks,
        {
            "task_id",
            "asset_id",
            "section_id",
            "department",
            "criticality",
            "urgency",
            "estimated_duration_min",
            "earliest_start",
            "deadline",
        },
        "maintenance_tasks.csv",
    )

    # Validate block columns
    check_columns(
        blocks,
        {
            "block_window_id",
            "section_id",
            "date",
            "start_time",
            "end_time",
            "availability_status",
        },
        "block_availability.csv",
    )

    # Validate train movement columns
    check_columns(
        trains,
        {
            "section_id",
            "entry_time",
            "exit_time",
        },
        "train_movements.csv",
    )

    # Convert maintenance timestamps
    tasks["earliest_start"] = pd.to_datetime(
        tasks["earliest_start"],
        format="mixed",
        errors="raise",
    )

    tasks["deadline"] = pd.to_datetime(
        tasks["deadline"],
        format="mixed",
        errors="raise",
    )

    # Convert block timestamps
    blocks["block_start"] = pd.to_datetime(
        blocks["date"].astype(str)
        + " "
        + blocks["start_time"].astype(str),
        format="mixed",
        errors="raise",
    )

    blocks["block_end"] = pd.to_datetime(
        blocks["date"].astype(str)
        + " "
        + blocks["end_time"].astype(str),
        format="mixed",
        errors="raise",
    )

    # Handle blocks that finish after midnight
    overnight = blocks["block_end"] <= blocks["block_start"]

    blocks.loc[overnight, "block_end"] += pd.Timedelta(days=1)

    # Convert train movement timestamps
    trains["entry_time"] = pd.to_datetime(
        trains["entry_time"],
        format="mixed",
        errors="raise",
    )

    trains["exit_time"] = pd.to_datetime(
        trains["exit_time"],
        format="mixed",
        errors="raise",
    )

    # Basic validation
    if tasks["task_id"].duplicated().any():
        raise ValueError("Duplicate task IDs found.")

    if blocks["block_window_id"].duplicated().any():
        raise ValueError("Duplicate block window IDs found.")

    if (tasks["estimated_duration_min"] <= 0).any():
        raise ValueError("Task duration must be positive.")

    if (trains["exit_time"] <= trains["entry_time"]).any():
        raise ValueError("Invalid train movement interval.")

    create_directories()

    print("\nCORE DATA LOADED")
    print("-------------------------")
    print("Maintenance tasks:", len(tasks))
    print("Block windows:", len(blocks))
    print("Train movements:", len(trains))

    return tasks, blocks, trains


def load_asset_features():
    """
    Load asset features used by the Random Forest model.
    """

    check_file(ASSET_FEATURE_FILE)

    features = pd.read_csv(ASSET_FEATURE_FILE)

    if "asset_id" not in features.columns:
        raise ValueError(
            "asset_features.csv must contain asset_id."
        )

    if features["asset_id"].duplicated().any():
        raise ValueError(
            "Duplicate asset IDs in asset_features.csv."
        )

    print("\nASSET FEATURES LOADED")
    print("-------------------------")
    print("Assets:", len(features))
    print("Features:", len(features.columns) - 1)

    return features


def load_optional_asset_data():
    """
    Load additional synthetic asset datasets when available.
    """

    datasets = {}

    optional_files = {
        "asset_master": ASSET_MASTER_FILE,
        "maintenance_history": MAINTENANCE_HISTORY_FILE,
        "risk_training": RISK_TRAINING_FILE,
    }

    for name, file_path in optional_files.items():

        if file_path.exists():
            datasets[name] = pd.read_csv(file_path)

            print(
                f"Loaded {name}:",
                len(datasets[name]),
                "rows",
            )

        else:
            print(
                f"Optional file not found: {file_path.name}"
            )

    return datasets


if __name__ == "__main__":

    tasks, blocks, trains = load_core_data()

    features = load_asset_features()

    optional_data = load_optional_asset_data()

    print("\nDATA LOADING COMPLETED")
