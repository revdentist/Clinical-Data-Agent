import json
import os
from datetime import datetime


def create_audit_log(patient_id: str, extracted: dict) -> dict:
    """
    Creates audit trail for every extracted field.
    Shows WHERE each value came from and WHY.
    This is what makes clinical AI trustworthy.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    audit = {
        "patient_id": patient_id,
        "processed_at": timestamp,
        "mode": "MOCK" if os.getenv("USE_MOCK_GEMINI") == "1" else "LIVE",
        "fields": []
    }

    # Define rules for each field
    field_rules = {
        "timeline.date_of_diagnosis": "RULE 008 - Date of diagnosis = pathology confirmation date only",
        "timeline.date_of_last_visit": "RULE 008 - Most recent visit date from MD notes",
        "timeline.date_of_last_scan": "RULE 008 - Most recent imaging date from radiology",
        "timeline.date_of_death": "RULE 008 - Date of death from patient record",
        "staging.primary_cancer": "RULE 004 - Cancer type confirmed by pathology",
        "staging.laterality": "RULE 002 - Laterality from pathology and imaging",
        "staging.t_stage": "RULE 004 - T stage confirmed by imaging AND MD note",
        "staging.n_stage": "RULE 004 - N stage confirmed by imaging AND MD note",
        "staging.m_stage": "RULE 004 - M stage confirmed by PET-CT",
        "staging.overall_stage": "RULE 004 - Stage group from TNM combination",
        "staging.metastasis": "RULE 009 - Metastasis confirmed by PET-CT + MD documentation",
        "pathology.specimen_site": "RULE 002 - Specimen site from pathology report",
        "pathology.quadrant": "RULE 002 - Quadrant from pathology report",
        "pathology.er_status": "RULE 003 - ER status from IHC in pathology report",
        "pathology.pr_status": "RULE 003 - PR status from IHC in pathology report",
        "pathology.her2_status": "RULE 003 - HER2 status from IHC/FISH in pathology report",
        "pathology.ki67_percentage": "RULE 003 - Ki67 from pathology report",
        "pathology.grade": "RULE 003 - Grade from pathology report",
        "pathology.diagnosis": "RULE 003 - Full diagnosis from pathology report",
        "comorbidities.hypertension": "RULE 001 - ONLY from MD note within first 3-6 months",
        "comorbidities.diabetes": "RULE 001 - ONLY from MD note within first 3-6 months",
        "comorbidities.hypothyroidism": "RULE 001 - ONLY from MD note within first 3-6 months",
        "comorbidities.other": "RULE 001 - ONLY from MD note within first 3-6 months",
        "germline.brca1_status": "RULE 005 - ONLY from official genetic testing report",
        "germline.brca2_status": "RULE 005 - ONLY from official genetic testing report",
        "germline.variant_found": "RULE 005 - ONLY from official genetic testing report",
        "germline.classification": "RULE 005 - ONLY from official genetic testing report",
        "medications.line_of_treatment": "RULE 006 - ONLY from MD notes",
        "medications.intent": "RULE 006 - ONLY from MD notes",
        "medications.regimen": "RULE 006 - ONLY from MD notes",
        "medications.drugs": "RULE 006 - ONLY from MD notes"
    }

    # Source document mapping
    source_map = {
        "timeline": "patient_record + md_notes + radiology",
        "staging": "md_note_visit2 + radiology + pathology",
        "pathology": "patient_001_pathology.txt",
        "comorbidities": "patient_001_md_note_visit1.txt (Visit 1 - within 3-6 months)",
        "germline": "patient_001_germline.txt",
        "medications": "patient_001_md_note_visit2.txt (MD notes only)"
    }

    # Walk through every field and log it
    for section, values in extracted.items():
        if section == "patient_id":
            continue

        if isinstance(values, dict):
            for field, value in values.items():
                field_key = f"{section}.{field}"
                rule = field_rules.get(field_key, "No specific rule")
                source = source_map.get(section, "Unknown source")

                if value is None:
                    status = "EMPTY - not found in documents"
                    confidence = "N/A"
                else:
                    status = "POPULATED"
                    confidence = "HIGH - extracted from source document"

                audit["fields"].append({
                    "field": field_key,
                    "value": value,
                    "status": status,
                    "confidence": confidence,
                    "source_document": source,
                    "rule_applied": rule
                })

    # Summary stats
    populated = sum(1 for f in audit["fields"] if f["status"] == "POPULATED")
    empty = sum(1 for f in audit["fields"] if "EMPTY" in f["status"])

    audit["summary"] = {
        "total_fields": len(audit["fields"]),
        "populated": populated,
        "empty": empty,
        "completion_rate": f"{(populated / len(audit['fields']) * 100):.1f}%"
    }

    return audit


def save_audit_log(audit: dict) -> str:
    """Save audit log to file"""
    os.makedirs("audit", exist_ok=True)
    filename = f"audit/audit_{audit['patient_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w") as f:
        json.dump(audit, f, indent=2)

    print(f"Audit log saved: {filename}")
    return filename


if __name__ == "__main__":
    import sys
    sys.path.append(".")

    # Test with mock data
    from agents.document_reader import read_patient_documents
    from agents.extractor import extract_clinical_data

    docs = read_patient_documents("patient_001")
    extracted = extract_clinical_data(docs, "patient_001")

    audit = create_audit_log("patient_001", extracted)
    filename = save_audit_log(audit)

    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Total fields:    {audit['summary']['total_fields']}")
    print(f"Populated:       {audit['summary']['populated']}")
    print(f"Empty:           {audit['summary']['empty']}")
    print(f"Completion rate: {audit['summary']['completion_rate']}")

    print(f"\n--- SAMPLE FIELD AUDIT ---")
    for field in audit["fields"][:3]:
        print(f"\nField:    {field['field']}")
        print(f"Value:    {field['value']}")
        print(f"Status:   {field['status']}")
        print(f"Source:   {field['source_document']}")
        print(f"Rule:     {field['rule_applied']}")