# Clinical Data Agent
### Built by someone who did this job manually

---

## Why I Built This

I spent a year doing clinical data abstraction for breast cancer research.

Every day I opened EPIC, read through radiology reports, pathology reports,
physician notes, genetic testing results — then manually filled REDCap forms
based on a strict set of abstraction rules.

The rules were not simple:
- Comorbidities only count if an MD documented them in the first 3-6 months
- Medications only from MD notes — never from pharmacy records
- Date of diagnosis means the pathology confirmation date — not imaging, not the first symptom
- Staging needs both imaging confirmation AND MD documentation — one source is not enough

I learned these rules the hard way. One wrong entry, one wrong source, one wrong date —
and the research data is corrupted.

After a year of this I left to pursue AI engineering.

Then one day it hit me: I could automate exactly what I used to do manually.

Not because I read a tutorial about healthcare AI.
Because I lived the problem.

---

## What It Does

This agent reads a breast cancer patient's EPIC documents and pre-fills their REDCap forms automatically.

**Input:** 5 clinical documents per patient
- Radiology report
- Pathology report
- MD progress notes (multiple visits)
- Germline genetic testing report

**Output:** Pre-filled REDCap form with:
- 26 fields auto-populated safely
- 5 high-stakes fields flagged for human review
- Full audit trail showing which document each field came from
- Which clinical rule was applied to each decision

**Time saved:** 3 hours per patient → 30 seconds per patient

---

## The Part That Actually Matters — The Rules

Any engineer can extract text from a document.

What makes clinical abstraction hard is knowing WHAT to extract, FROM WHERE, and WHEN.

I encoded 10 abstraction rules I know from experience:

| Rule | What It Does |
|------|-------------|
| RULE 001 | Comorbidities only from MD note in first 3-6 months from diagnosis |
| RULE 002 | Primary site must include laterality AND quadrant |
| RULE 003 | All IHC markers (ER, PR, HER2, Ki-67) from pathology report only |
| RULE 004 | Staging confirmed by BOTH imaging AND MD documentation |
| RULE 005 | Germline results only from official genetic testing report |
| RULE 006 | Medications only from MD notes — never pharmacy records |
| RULE 007 | BIRADS 4 or 5 required for imaging confirmation of malignancy |
| RULE 008 | Date of diagnosis = pathology confirmation date only |
| RULE 009 | Metastasis requires PET-CT confirmation + MD documentation |
| RULE 010 | ECOG performance status from MD notes only |

These are not arbitrary rules I invented.
These are the rules I followed every day for a year.

---

## How It Works

```
Patient documents arrive
        |
        v
DOCUMENT READER
Loads all EPIC documents for the patient
        |
        v
EXTRACTION AGENT  (Gemini AI)
Reads every document
Extracts structured clinical data
        |
        v
AUDIT LOGGER
Records every field:
- What value was extracted
- Which source document it came from
- Which rule applies to this field
        |
        v
GUARDRAILS ENGINE
Validates every extracted field:
- Was it from the right source?
- Was it from the right time window?
- Is confidence high enough to auto-populate?
- Does it need human review?
        |
        v
GUIDELINES RAG  (ChromaDB)
Retrieves the most relevant rules
for this specific patient case
        |
        v
REST API  (FastAPI)
Returns pre-filled form
with review requirements
and full audit trail
```

---

## The Audit Trail — Why It Exists

In healthcare, every data decision needs to be explainable.

Not just what was extracted — but why.

Every field in this system logs:

```json
{
  "field": "comorbidities.hypertension",
  "value": "Yes",
  "status": "POPULATED",
  "source_document": "patient_001_md_note_visit1.txt",
  "rule_applied": "RULE 001 - Only from MD note within first 3-6 months",
  "confidence": "HIGH - extracted from source document"
}
```

If the same comorbidity appeared in a nursing note from visit 6 — it gets rejected.
Not because the data is wrong. Because the source is wrong.
That distinction matters in clinical research.

---

## Results

| Metric | Value |
|--------|-------|
| Fields auto-populated | 26 of 31 |
| Fields flagged for human review | 5 of 31 |
| Fields rejected | 0 |
| Completion rate | 90.3% |
| Processing time | ~30 seconds |

The 5 fields that always require human review:
- Overall staging (affects treatment protocol)
- Metastasis status (affects treatment intent)
- Primary diagnosis (ground truth of the record)
- BRCA1 status (genetic counseling implications)
- Germline variant classification (clinical significance)

These fields are not wrong. They are flagged because the consequences of an error
are too significant to automate without a human checking.

Empty beats wrong in clinical data.

---

## Tech Stack

- **Python** — core language
- **FastAPI** — REST API
- **Google Gemini** — document extraction
- **ChromaDB** — vector storage for clinical guidelines
- **Pydantic** — strict data validation for REDCap forms
- **python-dotenv** — environment management

---

## API Endpoints

```
GET  /health                        — health check
POST /process                       — process patient documents
GET  /patient/{patient_id}/form     — get pre-filled REDCap form
```

Interactive docs at: `http://localhost:8000/docs`

---

## Setup

```bash
git clone https://github.com/revdentist/Clinical-Data-Agent
cd Clinical-Data-Agent
pip install -r requirements.txt

# Add your Gemini API key
cp .env.example .env
# Edit .env: GEMINI_API_KEY=your_key_here

# Run the pipeline
python pipeline.py

# Start the API
uvicorn api.main:app --reload
```

---

## Project Structure

```
clinical-agent/
├── agents/
│   ├── document_reader.py     loads EPIC documents
│   ├── extractor.py           AI extraction agent
│   └── guardrails.py          clinical rules engine
├── api/
│   └── main.py                FastAPI endpoints
├── audit/
│   └── logger.py              per-field audit trail
├── data/
│   ├── guidelines/            abstraction rules
│   └── patients/              synthetic patient documents
├── models/
│   └── redcap_form.py         Pydantic REDCap schema
├── rag/
│   └── guidelines_store.py    ChromaDB guidelines store
├── pipeline.py                full orchestration
└── README.md
```

---

## Important Note on Data

All patient data in this project is 100% synthetic.

I generated it using clinical domain knowledge — matching the structure and language
of real EPIC documents — but containing zero real patients.

No HIPAA-protected information was accessed or reproduced.

---

## What's Next

Things I want to build on top of this:

- **FHIR API integration** — replace text files with real EPIC FHIR endpoints
- **Longitudinal tracking** — PostgreSQL to track patients across years of follow-up
- **Expand cancer types** — lung, colorectal, lymphoma each have different guidelines
- **Confidence scoring** — dynamic thresholds based on field criticality
- **LangGraph orchestration** — replace sequential pipeline with conditional graph

---

## Who This Is For

BPOs like Omega Healthcare currently use human labor at scale for exactly this work.

This system does not replace clinical judgment.
It does the reading, the extracting, the form-filling.
The clinician reviews, verifies, approves.

The goal is not to remove humans from the loop.
The goal is to make their time worth more.

---

*Built in Chennai. Shipped at 1am. First real AI project.*
*From someone who did this job manually and got tired of it.*
