
import pandas as pd

from ortools.sat.python import cp_model

from backend.config import (
    CANDIDATE_OUTPUT_FILE,
    SCHEDULE_OUTPUT_FILE,
    UNSCHEDULED_OUTPUT_FILE,
    OUTPUT_DIR,
    TASK_FILE,
)

from optimization.constraints import (
    add_task_constraints,
    add_block_constraints,
)

from optimization.objective import (
    calculate_candidate_scores,
)


def timestamp_to_minutes(value):
    """
    Convert timestamp to integer minutes.
    """

    return int(
        pd.Timestamp(value).value // 60_000_000_000
    )


def minutes_to_timestamp(value):
    return pd.Timestamp(
        int(value),
        unit="m"
    )


def load_candidates():

    if not CANDIDATE_OUTPUT_FILE.exists():
        raise FileNotFoundError(
            "Candidate assignments not found. "
            "Run candidate generation first."
        )

    candidates_df = pd.read_csv(
        CANDIDATE_OUTPUT_FILE
    )

    if candidates_df.empty:
        return []

    required = {
        "task_id",
        "block_window_id",
        "duration_min",
        "candidate_start",
        "latest_start",
        "criticality",
        "urgency",
        "predicted_failure_probability",
    }

    missing = required - set(candidates_df.columns)

    if missing:
        raise ValueError(
            f"Candidate file missing columns: {sorted(missing)}"
        )

    candidates_df["candidate_start"] = pd.to_datetime(
        candidates_df["candidate_start"],
        format="mixed",
    )

    candidates_df["latest_start"] = pd.to_datetime(
        candidates_df["latest_start"],
        format="mixed",
    )

    return candidates_df.to_dict("records")


def build_and_solve(candidates):

    if not candidates:
        return [], "NO_CANDIDATES"

    model = cp_model.CpModel()

    task_vars = []
    intervals = []

    start_vars = []
    candidate_scores = []

    block_groups = {}

    for i, candidate in enumerate(candidates):

        duration = int(candidate["duration_min"])

        earliest_start = timestamp_to_minutes(
            candidate["candidate_start"]
        )

        latest_start = timestamp_to_minutes(
            candidate["latest_start"]
        )

        if earliest_start > latest_start:
            raise ValueError(
                f"Invalid candidate interval: {candidate['task_id']}"
            )

        # Whether this candidate assignment is selected
        selected = model.NewBoolVar(
            f"selected_{i}"
        )

        # Variable start time
        start = model.NewIntVar(
            earliest_start,
            latest_start,
            f"start_{i}",
        )

        # Optional interval: present only when selected
        interval = model.NewOptionalIntervalVar(
            start,
            duration,
            start + duration,
            selected,
            f"interval_{i}",
        )

        task_vars.append(selected)
        intervals.append(interval)
        start_vars.append(start)

        block_id = candidate["block_window_id"]

        block_groups.setdefault(
            block_id, []
        ).append(interval)

    # Constraint 1: A task can be selected at most once
    add_task_constraints(
        model,
        candidates,
        task_vars,
    )

    # Constraint 2: No overlapping maintenance in a block
    add_block_constraints(
        model,
        candidates,
        intervals,
    )

    # Objective: Maximize total task priority
    candidate_scores = calculate_candidate_scores(
        candidates
    )

    model.Maximize(
        sum(
            candidate_scores[i] * task_vars[i]
            for i in range(len(candidates))
        )
    )

    # Solve
    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    status_name = solver.StatusName(status)

    print("\nOPTIMIZATION STATUS:", status_name)

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        return [], status_name

    scheduled = []

    for i, candidate in enumerate(candidates):

        if solver.Value(task_vars[i]) == 1:

            start_minute = solver.Value(start_vars[i])

            duration = int(
                candidate["duration_min"]
            )

            end_minute = start_minute + duration

            scheduled.append({

                "task_id": candidate["task_id"],
                "asset_id": candidate["asset_id"],

                "block_window_id": candidate[
                    "block_window_id"
                ],

                "section_id": candidate["section_id"],
                "department": candidate["department"],

                "scheduled_start": minutes_to_timestamp(
                    start_minute
                ),

                "scheduled_end": minutes_to_timestamp(
                    end_minute
                ),

                "duration_min": duration,

                "criticality": candidate["criticality"],
                "urgency": candidate["urgency"],

                "predicted_failure_probability": candidate[
                    "predicted_failure_probability"
                ],

                "risk_level": candidate["risk_level"],

                "priority_score": candidate_scores[i],

            })

    return scheduled, status_name


def create_unscheduled(tasks, scheduled, candidates):

    scheduled_ids = {
        item["task_id"]
        for item in scheduled
    }

    candidate_ids = {
        item["task_id"]
        for item in candidates
    }

    unscheduled = []

    for _, task in tasks.iterrows():

        task_id = task["task_id"]

        if task_id in scheduled_ids:
            continue

        if task_id not in candidate_ids:
            reason = "NO_FEASIBLE_BLOCK"

        else:
            reason = "NOT_SELECTED_BY_OPTIMIZER"

        unscheduled.append({

            "task_id": task_id,
            "asset_id": task["asset_id"],
            "section_id": task["section_id"],

            "criticality": task["criticality"],
            "urgency": task["urgency"],

            "reason_code": reason,

        })

    return pd.DataFrame(unscheduled)


def main():

    print("\nRAILBLOCK OPTIMIZATION ENGINE")
    print("=" * 45)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    candidates = load_candidates()

    # Load original task information
    tasks = pd.read_csv(TASK_FILE)

    if not candidates:

        scheduled = []
        status = "NO_CANDIDATES"

    else:

        scheduled, status = build_and_solve(
            candidates
        )

    schedule_df = pd.DataFrame(scheduled)

    unscheduled_df = create_unscheduled(
        tasks,
        scheduled,
        candidates,
    )

    schedule_df.to_csv(
        SCHEDULE_OUTPUT_FILE,
        index=False,
    )

    unscheduled_df.to_csv(
        UNSCHEDULED_OUTPUT_FILE,
        index=False,
    )

    print("\nOPTIMIZATION SUMMARY")
    print("-" * 45)

    print("Solver status:", status)
    print("Total tasks:", len(tasks))
    print("Scheduled tasks:", len(schedule_df))
    print("Unscheduled tasks:", len(unscheduled_df))

    if len(schedule_df) > 0:

        print(
            "Blocks used:",
            schedule_df["block_window_id"].nunique()
        )

        print(
            "Average scheduled risk:",
            round(
                schedule_df[
                    "predicted_failure_probability"
                ].mean(),
                4,
            )
        )

    print("\nFiles saved:")
    print(SCHEDULE_OUTPUT_FILE)
    print(UNSCHEDULED_OUTPUT_FILE)


if __name__ == "__main__":
    main()
