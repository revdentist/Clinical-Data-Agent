import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import run_pipeline

app = FastAPI(
    title="Clinical Data Agent API",
    description="Automates breast cancer REDCap data abstraction from EPIC documents",
    version="1.0.0"
)


class PatientRequest(BaseModel):
    patient_id: str


class PipelineResponse(BaseModel):
    patient_id: str
    status: str
    fields_safe_to_populate: int
    fields_needing_review: int
    action_required: bool
    message: str


@app.get("/health")
def health_check():
    return {
        "status": "alive",
        "service": "Clinical Data Agent",
        "version": "1.0.0"
    }


@app.post("/process", response_model=PipelineResponse)
def process_patient(request: PatientRequest):
    """
    Process a patient's clinical documents.
    Extracts data and pre-fills REDCap form.
    Returns summary with fields ready for review.
    """
    try:
        result = run_pipeline(request.patient_id)

        return PipelineResponse(
            patient_id=result["patient_id"],
            status=result["status"],
            fields_safe_to_populate=result["fields_safe_to_populate"],
            fields_needing_review=result["guardrail_summary"]["human_review_required"],
            action_required=result["action_required"],
            message=f"Processing complete. {result['fields_safe_to_populate']} fields ready. {result['guardrail_summary']['human_review_required']} fields need review."
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found for patient {request.patient_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {str(e)}"
        )


@app.get("/patient/{patient_id}/form")
def get_filled_form(patient_id: str):
    """
    Get the pre-filled REDCap form for a patient.
    """
    try:
        result = run_pipeline(patient_id)
        return {
            "patient_id": patient_id,
            "form": result["extracted_data"],
            "guardrails": result["guardrail_summary"],
            "review_required": result["fields_needing_review"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patient/{patient_id}/guidelines")
def get_relevant_guidelines(patient_id: str):
    """
    Get the guidelines relevant to this patient's case.
    """
    try:
        result = run_pipeline(patient_id)
        return {
            "patient_id": patient_id,
            "relevant_guidelines": result["relevant_guidelines"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))