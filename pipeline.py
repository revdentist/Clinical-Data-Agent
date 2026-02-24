import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from agents.document_reader import read_patient_documents
from agents.extractor import extract_clinical_data
from agents.guardrails import apply_guardrails
from audit.logger import create_audit_log, save_audit_log
from rag.guidelines_store import query_guidelines


def run_pipeline(patient_id: str) -> dict:

    print(f"\n{'='*50}")
    print(f"CLINICAL DATA AGENT — Patient: {patient_id}")
    print(f"{'='*50}\n")

    print("STEP 1: Reading patient documents...")
    documents = read_patient_documents(patient_id)
    print(f"  Loaded {len(documents)} documents\n")

    print("STEP 2: Extracting clinical data...")
    extracted = extract_clinical_data(documents, patient_id)
    print(f"  Extraction complete\n")

    print("STEP 3: Creating audit trail...")
    audit = create_audit_log(patient_id, extracted)
    audit_file = save_audit_log(audit)
    print(f"  Audit saved: {audit_file}\n")

    print("STEP 4: Applying guardrails...")
    guardrail_report = apply_guardrails(extracted, audit["fields"])
    summary = guardrail_report["guardrail_summary"]
    print(f"  Approved:              {summary['approved']}")
    print(f"  Rejected:              {summary['rejected']}")
    print(f"  Human review needed:   {summary['human_review_required']}\n")

    print("STEP 5: Checking relevant guidelines...")
    cancer_type = extracted.get("staging", {}).get("primary_cancer", "breast cancer")
    guidelines = query_guidelines(f"{cancer_type} abstraction rules")
    print(f"  Found {len(guidelines)} relevant guidelines\n")

    final_result = {
        "patient_id": patient_id,
        "status": "COMPLETE",
        "extracted_data": extracted,
        "audit_file": audit_file,
        "guardrail_summary": summary,
        "relevant_guidelines": [g["rule"][:100] for g in guidelines],
        "action_required": summary["requires_manual_action"] > 0,
        "fields_safe_to_populate": summary["safe_to_auto_populate"],
        "fields_needing_review": guardrail_report["human_review_required"]
    }

    print(f"{'='*50}")
    print(f"PIPELINE COMPLETE")
    print(f"Safe to auto-populate:  {summary['safe_to_auto_populate']} fields")
    print(f"Needs human review:     {summary['human_review_required']} fields")
    print(f"Rejected:               {summary['rejected']} fields")
    print(f"{'='*50}\n")

    return final_result


if __name__ == "__main__":
    result = run_pipeline("patient_001")
    print("\n--- FINAL EXTRACTED FORM ---")
    print(json.dumps(result["extracted_data"], indent=2))