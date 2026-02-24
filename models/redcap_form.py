from pydantic import BaseModel
from typing import Optional

class PathologyFindings(BaseModel):
    specimen_site: Optional[str] = None
    quadrant: Optional[str] = None
    er_status: Optional[str] = None
    pr_status: Optional[str] = None
    her2_status: Optional[str] = None
    ki67_percentage: Optional[str] = None
    grade: Optional[str] = None
    diagnosis: Optional[str] = None

class StagingForm(BaseModel):
    primary_cancer: Optional[str] = None
    laterality: Optional[str] = None
    t_stage: Optional[str] = None
    n_stage: Optional[str] = None
    m_stage: Optional[str] = None
    overall_stage: Optional[str] = None
    metastasis: Optional[str] = None

class TimelineForm(BaseModel):
    date_of_diagnosis: Optional[str] = None
    date_of_last_visit: Optional[str] = None
    date_of_last_scan: Optional[str] = None
    date_of_death: Optional[str] = None

class ComorbidityForm(BaseModel):
    hypertension: Optional[str] = None
    diabetes: Optional[str] = None
    hypothyroidism: Optional[str] = None
    other: Optional[str] = None

class GermlineForm(BaseModel):
    brca1_status: Optional[str] = None
    brca2_status: Optional[str] = None
    variant_found: Optional[str] = None
    classification: Optional[str] = None

class MedicationForm(BaseModel):
    line_of_treatment: Optional[str] = None
    intent: Optional[str] = None
    regimen: Optional[str] = None
    drugs: Optional[str] = None

class REDCapForm(BaseModel):
    patient_id: str
    timeline: TimelineForm = TimelineForm()
    staging: StagingForm = StagingForm()
    pathology: PathologyFindings = PathologyFindings()
    comorbidities: ComorbidityForm = ComorbidityForm()
    germline: GermlineForm = GermlineForm()
    medications: MedicationForm = MedicationForm()


# Test it
if __name__ == "__main__":
    form = REDCapForm(patient_id="patient_001")
    print("REDCap form created successfully")
    print(form.model_dump())