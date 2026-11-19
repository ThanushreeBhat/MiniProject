
from fastapi import APIRouter, HTTPException

from backend.config import TASK_FILE

from backend.utils.response_formatter import (
    read_csv_records,
)


router = APIRouter()


@router.get("/tasks")
def get_tasks():

    try:

        records = read_csv_records(
            TASK_FILE
        )

        return {
            "total_tasks": len(records),
            "tasks": records,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/tasks/{task_id}")
def get_task(task_id: str):

    try:

        records = read_csv_records(
            TASK_FILE
        )

        result = [
            row for row in records
            if str(row["task_id"]) == task_id
        ]

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Maintenance task not found."
            )

        return result[0]

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
