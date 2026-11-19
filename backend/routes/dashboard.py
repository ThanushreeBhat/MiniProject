
from fastapi import APIRouter, HTTPException

from backend.config import (
    TASK_FILE,
    RISK_OUTPUT_FILE,
    SCHEDULE_OUTPUT_FILE,
    UNSCHEDULED_OUTPUT_FILE,
    VALIDATION_OUTPUT_FILE,
)

from backend.utils.response_formatter import (
    read_csv_records,
    read_json_file,
)

import pandas as pd


router = APIRouter()


@router.get("/dashboard")
def get_dashboard():

    try:

        tasks = pd.read_csv(TASK_FILE)
        risks = pd.read_csv(RISK_OUTPUT_FILE)
        schedule = pd.read_csv(SCHEDULE_OUTPUT_FILE)
        unscheduled = pd.read_csv(UNSCHEDULED_OUTPUT_FILE)

        validation = read_json_file(
            VALIDATION_OUTPUT_FILE
        )

        total_tasks = len(tasks)
        scheduled_count = len(schedule)
        unscheduled_count = len(unscheduled)

        risk_distribution = (
            risks["risk_level"]
            .value_counts()
            .to_dict()
        )

        return {

            "total_tasks": total_tasks,

            "scheduled_tasks": scheduled_count,

            "unscheduled_tasks": unscheduled_count,

            "schedule_coverage_percent": round(
                scheduled_count / total_tasks * 100,
                2
            ) if total_tasks else 0,

            "blocks_used": (
                int(schedule["block_window_id"].nunique())
                if not schedule.empty else 0
            ),

            "risk_distribution": risk_distribution,

            "validation_passed": validation[
                "validation_passed"
            ],

            "total_violations": validation[
                "total_violations"
            ],

        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
