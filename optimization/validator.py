
import json
import pandas as pd

from backend.config import (
    SCHEDULE_OUTPUT_FILE,
    VALIDATION_OUTPUT_FILE,
    OUTPUT_DIR,
)

from backend.utils.data_loader import load_core_data


def validate_schedule():

    print("\nRAILBLOCK INDEPENDENT VALIDATION")
    print("=" * 50)

    # 1. Load original input data
    tasks, blocks, trains = load_core_data()

    if not SCHEDULE_OUTPUT_FILE.exists():
        raise FileNotFoundError(
            "Optimized schedule not found."
        )

    schedule = pd.read_csv(SCHEDULE_OUTPUT_FILE)

    required_columns = {
        "task_id",
        "block_window_id",
        "section_id",
        "scheduled_start",
        "scheduled_end",
        "duration_min",
    }

    missing = required_columns - set(schedule.columns)

    if missing:
        raise ValueError(
            f"Schedule missing columns: {sorted(missing)}"
        )

    schedule["scheduled_start"] = pd.to_datetime(
        schedule["scheduled_start"],
        format="mixed",
    )

    schedule["scheduled_end"] = pd.to_datetime(
        schedule["scheduled_end"],
        format="mixed",
    )

    violations = []

    def add_violation(rule, task_id, message):

        violations.append({
            "rule": rule,
            "task_id": str(task_id),
            "message": message,
        })

    # 2. Duplicate task check

    duplicates = schedule[
        schedule["task_id"].duplicated(keep=False)
    ]

    for _, row in duplicates.iterrows():

        add_violation(
            "DUPLICATE_TASK",
            row["task_id"],
            "Task scheduled more than once."
        )

    # 3. Build lookup tables

    task_lookup = tasks.set_index("task_id").to_dict(
        orient="index"
    )

    block_lookup = blocks.set_index(
        "block_window_id"
    ).to_dict(orient="index")

    # 4. Task timing and block checks

    for _, row in schedule.iterrows():

        task_id = row["task_id"]
        block_id = row["block_window_id"]

        if task_id not in task_lookup:

            add_violation(
                "UNKNOWN_TASK",
                task_id,
                "Task does not exist in original dataset."
            )
            continue

        if block_id not in block_lookup:

            add_violation(
                "UNKNOWN_BLOCK",
                task_id,
                "Block does not exist in original dataset."
            )
            continue

        task = task_lookup[task_id]
        block = block_lookup[block_id]

        start = row["scheduled_start"]
        end = row["scheduled_end"]

        required_duration = int(
            task["estimated_duration_min"]
        )

        actual_duration = (
            end - start
        ).total_seconds() / 60

        # Positive interval check

        if end <= start:

            add_violation(
                "INVALID_INTERVAL",
                task_id,
                "Scheduled end is not after start."
            )

        # Duration check

        if actual_duration != required_duration:

            add_violation(
                "DURATION_MISMATCH",
                task_id,
                f"Expected {required_duration} minutes, "
                f"got {actual_duration} minutes."
            )

        # Earliest start check

        if start < task["earliest_start"]:

            add_violation(
                "EARLIEST_START",
                task_id,
                "Task starts before earliest permitted time."
            )

        # Deadline check

        if end > task["deadline"]:

            add_violation(
                "DEADLINE",
                task_id,
                "Task finishes after its deadline."
            )

        # Task section check

        if str(row["section_id"]) != str(task["section_id"]):

            add_violation(
                "TASK_SECTION_MISMATCH",
                task_id,
                "Schedule section differs from task section."
            )

        # Block section check

        if str(block["section_id"]) != str(task["section_id"]):

            add_violation(
                "BLOCK_SECTION_MISMATCH",
                task_id,
                "Assigned block belongs to another section."
            )

        # Block availability check

        if str(block["availability_status"]).strip().lower() != "available":

            add_violation(
                "BLOCK_UNAVAILABLE",
                task_id,
                "Task assigned to an unavailable block."
            )

        # Block timing check

        if (
            start < block["block_start"]
            or end > block["block_end"]
        ):

            add_violation(
                "BLOCK_TIMING",
                task_id,
                "Task exceeds assigned block window."
            )

    # 5. Maintenance overlap check

    for block_id, group in schedule.groupby("block_window_id"):

        ordered = group.sort_values("scheduled_start")

        previous_end = None
        previous_task = None

        for _, row in ordered.iterrows():

            if previous_end is not None:

                if row["scheduled_start"] < previous_end:

                    add_violation(
                        "MAINTENANCE_OVERLAP",
                        row["task_id"],
                        f"Overlaps with task {previous_task} "
                        f"in block {block_id}."
                    )

            if (
                previous_end is None
                or row["scheduled_end"] > previous_end
            ):

                previous_end = row["scheduled_end"]
                previous_task = row["task_id"]

    # 6. Train movement conflict check

    for _, row in schedule.iterrows():

        section_trains = trains[
            trains["section_id"].astype(str)
            == str(row["section_id"])
        ]

        for _, train in section_trains.iterrows():

            overlaps = (
                row["scheduled_start"] < train["exit_time"]
                and
                row["scheduled_end"] > train["entry_time"]
            )

            if overlaps:

                add_violation(
                    "TRAIN_CONFLICT",
                    row["task_id"],
                    "Maintenance overlaps a train movement."
                )

    # 7. Calculate validation summary

    total_tasks = len(tasks)
    scheduled_tasks = len(schedule)

    violation_count = len(violations)

    report = {

        "solver_output": str(SCHEDULE_OUTPUT_FILE),

        "total_tasks": int(total_tasks),

        "scheduled_tasks": int(scheduled_tasks),

        "unscheduled_tasks": int(
            total_tasks - scheduled_tasks
        ),

        "schedule_coverage_percent": round(
            scheduled_tasks / total_tasks * 100,
            2
        ) if total_tasks else 0,

        "total_violations": violation_count,

        "validation_passed": violation_count == 0,

        "violations": violations,

    }

    # 8. Map checks to actual violation codes

    check_rules = {

        "duplicate_tasks": [
            "DUPLICATE_TASK"
        ],

        "task_timing": [
            "EARLIEST_START",
            "INVALID_INTERVAL",
        ],

        "deadline": [
            "DEADLINE"
        ],

        "duration": [
            "DURATION_MISMATCH"
        ],

        "section_matching": [
            "TASK_SECTION_MISMATCH",
            "BLOCK_SECTION_MISMATCH",
        ],

        "block_availability": [
            "BLOCK_UNAVAILABLE"
        ],

        "block_timing": [
            "BLOCK_TIMING"
        ],

        "maintenance_overlap": [
            "MAINTENANCE_OVERLAP"
        ],

        "train_conflicts": [
            "TRAIN_CONFLICT"
        ],

        "task_existence": [
            "UNKNOWN_TASK"
        ],

        "block_existence": [
            "UNKNOWN_BLOCK"
        ],
    }

    report["checks"] = {

        name: not any(
            item["rule"] in rules
            for item in violations
        )

        for name, rules in check_rules.items()

    }

    # 9. Save validation report

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        VALIDATION_OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
        )

    # 10. Display results

    print("\nVALIDATION SUMMARY")
    print("-" * 50)

    print("Total tasks:", total_tasks)
    print("Scheduled tasks:", scheduled_tasks)

    print(
        "Coverage:",
        report["schedule_coverage_percent"],
        "%"
    )

    print("Total violations:", violation_count)

    print(
        "Validation passed:",
        report["validation_passed"]
    )

    print("\nINDIVIDUAL CHECKS")

    for name, passed in report["checks"].items():

        print(
            name,
            ":",
            "PASSED" if passed else "FAILED"
        )

    if violations:

        print("\nVIOLATIONS:")

        for violation in violations[:20]:

            print(
                violation["rule"],
                "|",
                violation["task_id"],
                "|",
                violation["message"],
            )

    else:

        print("\nAll implemented validation checks passed.")

    print("\nReport saved to:")
    print(VALIDATION_OUTPUT_FILE)

    return report


if __name__ == "__main__":
    validate_schedule()
