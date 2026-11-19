
from fastapi import APIRouter, HTTPException

from backend.config import EXPLANATION_OUTPUT_FILE

from backend.utils.response_formatter import (
    read_csv_records,
)


router = APIRouter()


@router.get("/explanations")
def get_explanations():

    try:

        records = read_csv_records(
            EXPLANATION_OUTPUT_FILE
        )

        return {
            "total_explanations": len(records),
            "explanations": records,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/explanations/{task_id}")
def get_task_explanation(task_id: str):

    try:

        records = read_csv_records(
            EXPLANATION_OUTPUT_FILE
        )

        result = [
            row for row in records
            if str(row["task_id"]) == task_id
        ]

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Task explanation not found."
            )

        return result[0]

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
