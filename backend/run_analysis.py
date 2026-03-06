from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from datetime import datetime, timezone
import json
from database import engine
from services.run_analysis_service import run_analysis_pipeline

router = APIRouter()


class AnalysisRunCreate(BaseModel):
    parameters_json: dict = Field(default_factory=dict)

@router.post("/businesses/{business_id}/analysis-runs")
def create_analysis_run(business_id: str, payload: AnalysisRunCreate):
    insert_run_query = text(
        """
        INSERT INTO analysis_run (business_id, parameters_json, status)
        VALUES (:business_id, :parameters_json, :status)
        RETURNING run_id
        """
    )

    mark_done_query = text(
        """
        UPDATE analysis_run
        SET status = :status,
            completed_at = :completed_at
        WHERE run_id = :run_id
        """
    )

    mark_failed_query = text(
        """
        UPDATE analysis_run
        SET status = 'failed',
            completed_at = :completed_at,
            parameters_json = jsonb_set(
              COALESCE(parameters_json, '{}'::jsonb),
              '{error}',
              to_jsonb(:error_msg::text),
              true
            )
        WHERE run_id = :run_id
        """
    )

    try:
        # Create analysis_run row
        with engine.begin() as conn:
            result = conn.execute(
                insert_run_query,
                {
                    "business_id": business_id,
                    "status": "running",
                    "parameters_json": json.dumps(payload.parameters_json),
                },
            )
        
        # Run pipeline to write to topic
        new_run_id = result.scalar_one()
        run_analysis_pipeline(
            business_id = business_id,
            parameters = payload.parameters_json,
            run_id = new_run_id
        )
        print("Row of result: ", new_run_id)

        # If success, mark as complete
        with engine.begin() as conn:
            conn.execute(
                mark_done_query,
                {
                    "run_id": new_run_id,
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc)
                }
            )

    except Exception as e:
        # Handling error, if insert gone wrong mark as failed
        with engine.begin() as conn:
            conn.execute(
                mark_failed_query,
                {
                    "run_id": new_run_id,
                    "completed_at": datetime.now(timezone.utc),
                    "error_msg": str(e)
                }
            )
        print("Row of result after line 85: ", 
        )
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    
