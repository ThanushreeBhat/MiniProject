
import pandas as pd

from backend.config import (
    TASK_FILE,
    RISK_OUTPUT_FILE,
    CANDIDATE_OUTPUT_FILE,
    SCHEDULE_OUTPUT_FILE,
    UNSCHEDULED_OUTPUT_FILE,
    EXPLANATION_OUTPUT_FILE,
    OUTPUT_DIR,
)


def priority_score(criticality, urgency, risk):

    criticality_weights = {
        "critical": 100,
        "high": 70,
        "medium": 40,
        "low": 20,
    }

    urgency_weights = {
        "high": 50,
        "medium": 25,
        "low": 10,
    }

    criticality = str(criticality).strip().lower()
    urgency = str(urgency).strip().lower()

    return (
        criticality_weights.get(criticality, 0)
        + urgency_weights.get(urgency, 0)
        + round(float(risk) * 100)
    )


def format_time(value):

    if pd.isna(value):
        return "Unknown"

    return pd.Timestamp(value).strftime(
        "%d-%m-%Y %H:%M"
    )


def explain_scheduled(task, schedule, risk, candidates):

    task_id = str(task["task_id"])

    probability = float(
        risk["predicted_failure_probability"]
    )

    level = risk["risk_level"]

    score = priority_score(
        task["criticality"],
        task["urgency"],
        probability,
    )

    start = format_time(schedule["scheduled_start"])
    end = format_time(schedule["scheduled_end"])

    explanation = (
        f"Task {task_id} was selected by the risk-aware "
        f"optimizer and assigned to block "
        f"{schedule['block_window_id']} in section "
        f"{task['section_id']}. "
        f"The maintenance interval is from {start} to {end}. "
        f"The task has {task['criticality']} criticality "
        f"and {task['urgency']} urgency. "
        f"The Random Forest predicted a "
        f"{probability:.2%} failure probability, "
        f"classified as {level} risk. "
        f"Its calculated priority score is {score}. "
        f"The selected assignment was feasible under the "
        f"candidate-generation rules and the optimizer's "
        f"implemented constraints."
    )

    return explanation, score


def explain_unscheduled(task, reason, candidate_count, risk):

    task_id = str(task["task_id"])

    probability = float(
        risk["predicted_failure_probability"]
    )

    level = risk["risk_level"]

    score = priority_score(
        task["criticality"],
        task["urgency"],
        probability,
    )

    if candidate_count == 0:

        explanation = (
            f"Task {task_id} was not scheduled because "
            f"no feasible candidate block was generated. "
            f"The available block windows did not provide "
            f"a suitable train-free interval that satisfied "
            f"the task's section, duration, earliest-start "
            f"and deadline requirements. "
            f"Its predicted failure probability is "
            f"{probability:.2%} ({level} risk)."
        )

        reason = "NO_FEASIBLE_BLOCK"

    else:

        explanation = (
            f"Task {task_id} had {candidate_count} feasible "
            f"candidate assignment(s), but the optimizer "
            f"did not select it in the final schedule. "
            f"The optimizer selected a combination of tasks "
            f"that maximized the implemented total priority "
            f"objective while respecting its scheduling "
            f"constraints. This does not by itself prove "
            f"that another task directly blocked this task. "
            f"Its predicted failure probability is "
            f"{probability:.2%} ({level} risk)."
        )

        reason = "NOT_SELECTED_BY_OPTIMIZER"

    return explanation, score, reason


def generate_explanations():

    print("\nRAILBLOCK EXPLANATION ENGINE")
    print("=" * 50)

    # Load source files
    required_files = [
        TASK_FILE,
        RISK_OUTPUT_FILE,
        CANDIDATE_OUTPUT_FILE,
        SCHEDULE_OUTPUT_FILE,
        UNSCHEDULED_OUTPUT_FILE,
    ]

    for file_path in required_files:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

    tasks = pd.read_csv(TASK_FILE)

    risks = pd.read_csv(RISK_OUTPUT_FILE)

    candidates = pd.read_csv(CANDIDATE_OUTPUT_FILE)

    schedule = pd.read_csv(SCHEDULE_OUTPUT_FILE)

    unscheduled = pd.read_csv(UNSCHEDULED_OUTPUT_FILE)

    # Normalize IDs for reliable matching
    for df in [tasks, risks, candidates, schedule, unscheduled]:

        if "task_id" in df.columns:
            df["task_id"] = df["task_id"].astype(str)

        if "asset_id" in df.columns:
            df["asset_id"] = df["asset_id"].astype(str)

    risks["asset_id"] = risks["asset_id"].astype(str)

    # Create lookup dictionaries
    risk_lookup = risks.set_index("asset_id").to_dict(
        orient="index"
    )

    schedule_lookup = schedule.set_index("task_id").to_dict(
        orient="index"
    )

    unscheduled_lookup = unscheduled.set_index(
        "task_id"
    ).to_dict(orient="index")

    candidate_counts = (
        candidates.groupby("task_id").size().to_dict()
        if not candidates.empty
        else {}
    )

    results = []

    for _, task in tasks.iterrows():

        task_id = str(task["task_id"])
        asset_id = str(task["asset_id"])

        if asset_id not in risk_lookup:
            raise ValueError(
                f"Risk prediction missing for asset {asset_id}"
            )

        risk = risk_lookup[asset_id]

        candidate_count = int(
            candidate_counts.get(task_id, 0)
        )

        # Scheduled task
        if task_id in schedule_lookup:

            scheduled = schedule_lookup[task_id]

            explanation, score = explain_scheduled(
                task,
                scheduled,
                risk,
                candidate_count,
            )

            status = "SCHEDULED"
            reason_code = "SCHEDULED"

            block_id = scheduled["block_window_id"]
            start = scheduled["scheduled_start"]
            end = scheduled["scheduled_end"]

        # Unscheduled task
        else:

            unscheduled_info = unscheduled_lookup.get(
                task_id, {}
            )

            reason_code = unscheduled_info.get(
                "reason_code",
                "NOT_SELECTED_BY_OPTIMIZER"
            )

            explanation, score, reason_code = explain_unscheduled(
                task,
                reason_code,
                candidate_count,
                risk,
            )

            status = "UNSCHEDULED"
            block_id = None
            start = None
            end = None

        results.append({

            "task_id": task_id,
            "asset_id": asset_id,

            "status": status,
            "reason_code": reason_code,

            "section_id": task["section_id"],
            "department": task["department"],

            "criticality": task["criticality"],
            "urgency": task["urgency"],

            "predicted_failure_probability": (
                risk["predicted_failure_probability"]
            ),

            "risk_level": risk["risk_level"],

            "priority_score": score,

            "candidate_block_count": candidate_count,

            "assigned_block": block_id,
            "scheduled_start": start,
            "scheduled_end": end,

            "explanation": explanation,

        })

    explanation_df = pd.DataFrame(results)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    explanation_df.to_csv(
        EXPLANATION_OUTPUT_FILE,
        index=False
    )

    # Summary
    print("\nEXPLANATION SUMMARY")
    print("-" * 50)

    print("Tasks explained:", len(explanation_df))

    print(
        "Scheduled:",
        (explanation_df["status"] == "SCHEDULED").sum()
    )

    print(
        "Unscheduled:",
        (explanation_df["status"] == "UNSCHEDULED").sum()
    )

    print("\nReason distribution:")

    print(
        explanation_df["reason_code"]
        .value_counts()
        .to_string()
    )

    print("\nExample explanations:")

    for _, row in explanation_df.head(3).iterrows():

        print("\n", row["task_id"])
        print(row["explanation"])

    print("\nSaved to:")
    print(EXPLANATION_OUTPUT_FILE)

    return explanation_df


if __name__ == "__main__":
    generate_explanations()
