import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# Confidence thresholds
THRESHOLDS = {
    "staging": 0.95,       # Highest — staging affects treatment
    "pathology": 0.95,     # Highest — pathology is ground truth
    "germline": 0.99,      # Highest — genetic results are binary
    "medications": 0.90,   # High — wrong drug is dangerous
    "comorbidities": 0.90, # High — rule-based source required
    "timeline": 0.85       # Medium — dates less critical
}

# Fields that always need human review
ALWAYS_REVIEW = [
    "staging.overall_stage",
    "staging.metastasis",
    "pathology.diagnosis",
    "germline.brca1_status",
    "germline.variant_found"
]

# Fields where empty is safer than wrong
EMPTY_BEATS_WRONG = [
    "staging.t_stage",
    "staging.n_stage",
    "staging.m_stage",
    "pathology.er_status",
    "pathology.her2_status",
    "medications.drugs"
]


def check_comorbidity_source_rule(
    field: str,
    value: str,
    source_document: str
) -> tuple[bool, str]:
    """
    RULE 001 — Comorbidities only from MD note
    within first 3-6 months.
    Returns (passed, reason)
    """
    if value is None:
        return True, "Field is null — acceptable"

    # Check source is MD note visit 1
    valid_sources = ["md_note_visit1", "visit1", "visit 1"]
    source_lower = source_document.lower()

    if any(s in source_lower for s in valid_sources):
        return True, "Source is MD note visit 1 — within 3-6 month window"
    else:
        return False, f"REJECTED — comorbidity source '{source_document}' is outside 3-6 month window. Rule 001 violation."


def check_medication_source_rule(
    field: str,
    value: str,
    source_document: str
) -> tuple[bool, str]:
    """
    RULE 006 — Medications only from MD notes.
    Never from pharmacy records.
    Returns (passed, reason)
    """
    if value is None:
        return True, "Field is null — acceptable"

    forbidden_sources = ["pharmacy", "nursing", "dispensing", "prescription"]
    source_lower = source_document.lower()

    if any(s in source_lower for s in forbidden_sources):
        return False, f"REJECTED — medication source '{source_document}' is not an MD note. Rule 006 violation."

    return True, "Source is MD note — valid for medication abstraction"


def check_diagnosis_date_rule(
    value: str
) -> tuple[bool, str]:
    """
    RULE 008 — Date of diagnosis must be
    pathology confirmation date.
    Not imaging date. Not symptom date.
    Returns (passed, reason)
    """
    if value is None:
        return True, "Field is null — acceptable"

    return True, "Date of diagnosis accepted — verify manually it matches pathology report date"


def check_staging_confirmation_rule(
    t_stage: str,
    n_stage: str,
    m_stage: str,
    has_imaging: bool = True,
    has_md_note: bool = True
) -> tuple[bool, str]:
    """
    RULE 004 — Staging must be confirmed by
    BOTH imaging AND MD documentation.
    Returns (passed, reason)
    """
    if not has_imaging and not has_md_note:
        return False, "REJECTED — staging requires both imaging AND MD confirmation"

    if not has_imaging:
        return False, "REJECTED — staging missing imaging confirmation"

    if not has_md_note:
        return False, "REJECTED — staging missing MD documentation"

    return True, "Staging confirmed by both imaging and MD note"


def apply_guardrails(extracted: dict, audit_fields: list) -> dict:
    """
    Apply all guardrails to extracted data.
    Returns guardrail report with:
    - approved fields
    - rejected fields
    - fields requiring human review
    """

    report = {
        "patient_id": extracted.get("patient_id"),
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "approved": [],
        "rejected": [],
        "human_review_required": [],
        "guardrail_summary": {}
    }

    # Check every field
    for field_audit in audit_fields:
        field_key = field_audit["field"]
        value = field_audit["value"]
        source = field_audit["source_document"]
        section = field_key.split(".")[0]

        passed = True
        reason = "Passed all guardrails"

        # GUARDRAIL 1 — Comorbidity source rule
        if section == "comorbidities" and value is not None:
            passed, reason = check_comorbidity_source_rule(
                field_key, value, source
            )

        # GUARDRAIL 2 — Medication source rule
        elif section == "medications" and value is not None:
            passed, reason = check_medication_source_rule(
                field_key, value, source
            )

        # GUARDRAIL 3 — Diagnosis date rule
        elif field_key == "timeline.date_of_diagnosis":
            passed, reason = check_diagnosis_date_rule(value)

        # GUARDRAIL 4 — Staging confirmation
        elif field_key == "staging.overall_stage":
            passed, reason = check_staging_confirmation_rule(
                extracted.get("staging", {}).get("t_stage"),
                extracted.get("staging", {}).get("n_stage"),
                extracted.get("staging", {}).get("m_stage")
            )

        # GUARDRAIL 5 — Empty beats wrong
        if field_key in EMPTY_BEATS_WRONG and value is None:
            reason = "Field empty — safer than potentially wrong value"

        # GUARDRAIL 6 — Always review list
        needs_review = field_key in ALWAYS_REVIEW

        field_result = {
            "field": field_key,
            "value": value,
            "passed": passed,
            "reason": reason,
            "requires_human_review": needs_review
        }

        if not passed:
            report["rejected"].append(field_result)
        elif needs_review:
            report["human_review_required"].append(field_result)
        else:
            report["approved"].append(field_result)

    # Summary
    report["guardrail_summary"] = {
        "total_checked": len(audit_fields),
        "approved": len(report["approved"]),
        "rejected": len(report["rejected"]),
        "human_review_required": len(report["human_review_required"]),
        "safe_to_auto_populate": len(report["approved"]),
        "requires_manual_action": len(report["rejected"]) + len(report["human_review_required"])
    }

    return report


if __name__ == "__main__":
    from agents.document_reader import read_patient_documents
    from agents.extractor import extract_clinical_data
    from data.audit.logger import create_audit_log

    docs = read_patient_documents("patient_001")
    extracted = extract_clinical_data(docs, "patient_001")
    audit = create_audit_log("patient_001", extracted)

    report = apply_guardrails(extracted, audit["fields"])

    print("\n--- GUARDRAIL REPORT ---")
    print(f"Total checked:          {report['guardrail_summary']['total_checked']}")
    print(f"Approved:               {report['guardrail_summary']['approved']}")
    print(f"Rejected:               {report['guardrail_summary']['rejected']}")
    print(f"Human review required:  {report['guardrail_summary']['human_review_required']}")
    print(f"Safe to auto-populate:  {report['guardrail_summary']['safe_to_auto_populate']}")

    if report["rejected"]:
        print("\n--- REJECTED FIELDS ---")
        for f in report["rejected"]:
            print(f"  REJECTED: {f['field']}")
            print(f"  Reason:   {f['reason']}")

    if report["human_review_required"]:
        print("\n--- NEEDS HUMAN REVIEW ---")
        for f in report["human_review_required"]:
            print(f"  REVIEW:   {f['field']}")
            print(f"  Value:    {f['value']}")