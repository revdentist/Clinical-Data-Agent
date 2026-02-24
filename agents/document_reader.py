import os

def read_patient_documents(patient_id: str) -> dict:
    """
    Read all documents for a patient.
    Returns dictionary of document_type → content.
    """
    base_path = "data/patients"
    documents = {}

    for filename in os.listdir(base_path):
        if patient_id in filename:
            filepath = os.path.join(base_path, filename)
            with open(filepath, "r") as f:
                content = f.read()

            doc_type = filename.replace(f"{patient_id}_", "").replace(".txt", "")
            documents[doc_type] = content
            # Using plain ASCII symbols to avoid Windows console encoding issues
            print(f"[OK] Loaded: {filename}")

    return documents


# Test it
if __name__ == "__main__":
    docs = read_patient_documents("patient_001")
    print(f"\nLoaded {len(docs)} documents:")
    for doc_type, content in docs.items():
        print(f"  - {doc_type}: {len(content)} characters")