
from fastapi import APIRouter, HTTPException

from backend.config import (
    SCHEDULE_OUTPUT_FILE,
    UNSCHEDULED_OUTPUT_FILE,
)

from backend.utils.response_formatter import (
    read_csv_records,
)


router = APIRouter()


@router.get("/schedule")
def get_schedule():

    try:

        records = read_csv_records(
            SCHEDULE_OUTPUT_FILE
        )

        return {
            "total_scheduled": len(records),
            "schedule": records,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/unscheduled")
def get_unscheduled():

    try:

        records = read_csv_records(
            UNSCHEDULED_OUTPUT_FILE
        )

        return {
            "total_unscheduled": len(records),
            "tasks": records,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
