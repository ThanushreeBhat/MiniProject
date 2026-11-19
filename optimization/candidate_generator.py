
import pandas as pd

from backend.utils.data_loader import load_core_data
from backend.config import (
    RISK_OUTPUT_FILE,
    CANDIDATE_OUTPUT_FILE,
    OUTPUT_DIR,
)


def load_risk_predictions():

    if not RISK_OUTPUT_FILE.exists():
        raise FileNotFoundError(
            f"Risk predictions not found: {RISK_OUTPUT_FILE}"
        )

    risk = pd.read_csv(RISK_OUTPUT_FILE)

    required = {
        "asset_id",
        "predicted_failure_probability",
        "risk_level",
    }

    missing = required - set(risk.columns)

    if missing:
        raise ValueError(
            f"Risk file missing columns: {sorted(missing)}"
        )

    if risk["asset_id"].duplicated().any():
        raise ValueError("Duplicate asset IDs in risk predictions.")

    risk["predicted_failure_probability"] = pd.to_numeric(
        risk["predicted_failure_probability"],
        errors="raise",
    )

    if not risk["predicted_failure_probability"].between(0, 1).all():
        raise ValueError("Risk probabilities must be between 0 and 1.")

    return risk


def get_free_intervals(block, section_trains):

    """
    Return the portions of a block not occupied by train movements.
    """

    block_start = block["block_start"]
    block_end = block["block_end"]

    occupied = []

    for _, train in section_trains.iterrows():

        train_start = max(
            train["entry_time"],
            block_start
        )

        train_end = min(
            train["exit_time"],
            block_end
        )

        if train_start < train_end:
            occupied.append((train_start, train_end))

    # Sort and merge overlapping train intervals
    occupied.sort(key=lambda interval: interval[0])

    merged = []

    for start, end in occupied:

        if not merged or start > merged[-1][1]:
            merged.append([start, end])

        else:
            merged[-1][1] = max(
                merged[-1][1],
                end
            )

    # Find gaps between train movements
    free_intervals = []
    current = block_start

    for start, end in merged:

        if current < start:
            free_intervals.append((current, start))

        current = max(current, end)

    if current < block_end:
        free_intervals.append((current, block_end))

    return free_intervals


def generate_candidates(tasks, blocks, trains, risk):

    candidates = []

    # Attach model risk predictions to maintenance tasks
    tasks = tasks.merge(
        risk[
            [
                "asset_id",
                "predicted_failure_probability",
                "risk_level",
            ]
        ],
        on="asset_id",
        how="left",
        validate="many_to_one",
    )

    if tasks["predicted_failure_probability"].isna().any():
        missing_assets = tasks.loc[
            tasks["predicted_failure_probability"].isna(),
            "asset_id",
        ].unique()

        raise ValueError(
            "Missing risk predictions for assets: "
            + str(missing_assets.tolist())
        )

    for _, task in tasks.iterrows():

        duration = int(task["estimated_duration_min"])

        earliest = task["earliest_start"]
        deadline = task["deadline"]

        section = str(task["section_id"])

        # Only blocks belonging to the task's section
        section_blocks = blocks[
            blocks["section_id"].astype(str) == section
        ]

        # Only train movements in the same section
        section_trains = trains[
            trains["section_id"].astype(str) == section
        ]

        for _, block in section_blocks.iterrows():

            if str(block["availability_status"]).strip().lower() != "available":
                continue

            block_start = block["block_start"]
            block_end = block["block_end"]

            # Ignore blocks outside task's time window
            if block_end <= earliest or block_start >= deadline:
                continue

            free_intervals = get_free_intervals(
                block,
                section_trains
            )

            for free_start, free_end in free_intervals:

                # Earliest permitted start
                possible_start = max(
                    free_start,
                    earliest
                )

                # Latest permitted start
                latest_start = min(
                    free_end - pd.Timedelta(minutes=duration),
                    deadline - pd.Timedelta(minutes=duration)
                )

                if possible_start > latest_start:
                    continue

                candidates.append({

                    "task_id": task["task_id"],
                    "asset_id": task["asset_id"],

                    "block_window_id": block["block_window_id"],
                    "section_id": section,
                    "department": task["department"],

                    "duration_min": duration,

                    "candidate_start": possible_start,
                    "latest_start": latest_start,

                    "candidate_end": (
                        possible_start
                        + pd.Timedelta(minutes=duration)
                    ),

                    "free_interval_start": free_start,
                    "free_interval_end": free_end,

                    "criticality": task["criticality"],
                    "urgency": task["urgency"],

                    "predicted_failure_probability": (
                        task["predicted_failure_probability"]
                    ),

                    "risk_level": task["risk_level"],

                })

    return pd.DataFrame(candidates)


def main():

    print("\nRAILBLOCK CANDIDATE GENERATION")
    print("=" * 45)

    tasks, blocks, trains = load_core_data()

    risk = load_risk_predictions()

    candidates = generate_candidates(
        tasks,
        blocks,
        trains,
        risk,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    candidates.to_csv(
        CANDIDATE_OUTPUT_FILE,
        index=False,
    )

    print("\nCANDIDATE GENERATION COMPLETED")
    print("-" * 45)

    print("Maintenance tasks:", len(tasks))
    print("Available blocks:", len(blocks))
    print("Train movements:", len(trains))
    print("Candidate assignments:", len(candidates))

    print(
        "Tasks with candidates:",
        candidates["task_id"].nunique()
        if not candidates.empty else 0
    )

    print(
        "Tasks without candidates:",
        len(tasks) - (
            candidates["task_id"].nunique()
            if not candidates.empty else 0
        )
    )

    print("\nSaved to:")
    print(CANDIDATE_OUTPUT_FILE)


if __name__ == "__main__":
    main()
