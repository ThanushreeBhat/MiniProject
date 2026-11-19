
from fastapi import APIRouter, HTTPException

from backend.config import VALIDATION_OUTPUT_FILE

from backend.utils.response_formatter import (
    read_json_file,
)


router = APIRouter()


@router.get("/validation")
def get_validation():

    try:

        return read_json_file(
            VALIDATION_OUTPUT_FILE
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
