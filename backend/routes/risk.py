
from fastapi import APIRouter, HTTPException

from backend.config import RISK_OUTPUT_FILE

from backend.utils.response_formatter import (
    read_csv_records,
)


router = APIRouter()


@router.get("/risks")
def get_risks():

    try:

        records = read_csv_records(
            RISK_OUTPUT_FILE
        )

        return {
            "total_assets": len(records),
            "predictions": records,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/risks/{asset_id}")
def get_asset_risk(asset_id: str):

    try:

        records = read_csv_records(
            RISK_OUTPUT_FILE
        )

        result = [
            row for row in records
            if str(row["asset_id"]) == asset_id
        ]

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Asset risk prediction not found."
            )

        return result[0]

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
