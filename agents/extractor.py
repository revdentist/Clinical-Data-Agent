import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

USE_MOCK = os.getenv("USE_MOCK_GEMINI", "0") == "1"

if not USE_MOCK:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def mock_extraction(patient_id: str) -> dict:
    """
    Returns hardcoded realistic extraction
    for patient_001 breast cancer case.
    Used for testing pipeline without API calls.
    """
    return {
        "patient_id": patient_id,
        "timeline": {
            "date_of_diagnosis": "2024-02-18",
            "date_of_last_visit": "2024-03-15",
            "date_of_last_scan": "2024-02-10",
            "date_of_death": None
        },
        "staging": {
            "primary_cancer": "Invasive Ductal Carcinoma",
            "laterality": "Left",
            "t_stage": "T2",
            "n_stage": "N1",
            "m_stage": "M0",
            "overall_stage": "IIB",
            "metastasis": "No"
        },
        "pathology": {
            "specimen_site": "Left breast",
            "quadrant": "Upper outer quadrant",
            "er_status": "Positive - 85%",
            "pr_status": "Positive - 60%",
            "her2_status": "Negative",
            "ki67_percentage": "35%",
            "grade": "Grade 3 - Nottingham score 8/9",
            "diagnosis": "Invasive Ductal Carcinoma, ER+, PR+, HER2-"
        },
        "comorbidities": {
            "hypertension": "Yes - documented in visit 1 (within 3-6 months)",
            "diabetes": None,
            "hypothyroidism": "Yes - documented in visit 1 (within 3-6 months)",
            "other": None
        },
        "germline": {
            "brca1_status": "Pathogenic variant detected",
            "brca2_status": "Negative",
            "variant_found": "c.5266dupC (p.Gln1756Profs*74)",
            "classification": "Pathogenic - HBOC Syndrome"
        },
        "medications": {
            "line_of_treatment": "1st line",
            "intent": "Neoadjuvant",
            "regimen": "Dose Dense AC-T",
            "drugs": "Doxorubicin, Cyclophosphamide, Paclitaxel"
        }
    }


def extract_clinical_data(documents: dict, patient_id: str) -> dict:

    if USE_MOCK:
        print("MOCK MODE — skipping API call")
        return mock_extraction(patient_id)

    combined_docs = ""
    for doc_type, content in documents.items():
        combined_docs += f"\n\n--- {doc_type.upper()} ---\n{content}"

    prompt = f"""You are a clinical data abstractor.
Read these patient documents and extract information
to fill the REDCap form fields.

PATIENT DOCUMENTS:
{combined_docs}

Return ONLY raw JSON. No markdown. No code fences.
Start directly with {{

{{
  "timeline": {{
    "date_of_diagnosis": "date pathology confirmed cancer or null",
    "date_of_last_visit": "most recent visit date or null",
    "date_of_last_scan": "most recent imaging date or null",
    "date_of_death": "date of death or null"
  }},
  "staging": {{
    "primary_cancer": "cancer type or null",
    "laterality": "left/right/bilateral or null",
    "t_stage": "T stage or null",
    "n_stage": "N stage or null",
    "m_stage": "M stage or null",
    "overall_stage": "stage group or null",
    "metastasis": "yes/no or null"
  }},
  "pathology": {{
    "specimen_site": "biopsy site or null",
    "quadrant": "breast quadrant or null",
    "er_status": "ER positive/negative or null",
    "pr_status": "PR positive/negative or null",
    "her2_status": "HER2 positive/negative or null",
    "ki67_percentage": "Ki67 percentage or null",
    "grade": "tumor grade or null",
    "diagnosis": "full pathology diagnosis or null"
  }},
  "comorbidities": {{
    "hypertension": "yes/no ONLY if MD note first 3-6 months or null",
    "diabetes": "yes/no ONLY if MD note first 3-6 months or null",
    "hypothyroidism": "yes/no ONLY if MD note first 3-6 months or null",
    "other": "other comorbidities from first 3-6 months MD note or null"
  }},
  "germline": {{
    "brca1_status": "pathogenic/negative or null",
    "brca2_status": "pathogenic/negative or null",
    "variant_found": "variant name or null",
    "classification": "classification or null"
  }},
  "medications": {{
    "line_of_treatment": "1st line/2nd line or null",
    "intent": "neoadjuvant/adjuvant/palliative or null",
    "regimen": "regimen name or null",
    "drugs": "list of drugs or null"
  }}
}}

CRITICAL RULES:
1. Comorbidities ONLY from MD notes in first 3-6 months
2. Medications ONLY from MD notes
3. Date of diagnosis = pathology confirmation date only
4. If not found use null
5. Never guess"""

    print("Sending documents to Gemini for extraction...")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    raw = response.text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    print("Gemini responded. Parsing...")
    extracted = json.loads(raw)
    extracted["patient_id"] = patient_id

    return extracted


if __name__ == "__main__":
    from agents.document_reader import read_patient_documents

    docs = read_patient_documents("patient_001")
    print(f"Loaded {len(docs)} documents\n")

    result = extract_clinical_data(docs, "patient_001")

    print("\n--- EXTRACTED REDCAP DATA ---")
    print(json.dumps(result, indent=2))