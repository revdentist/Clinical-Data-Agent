import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import chromadb

# Create persistent ChromaDB store
def get_guidelines_store():
    client = chromadb.PersistentClient(path="./rag/guidelines_db")
    collection = client.get_or_create_collection(
        name="breast_cancer_guidelines"
    )
    return collection


def load_guidelines_into_store():
    """
    Load guidelines from text file into ChromaDB.
    Run this ONCE to populate the store.
    """
    collection = get_guidelines_store()

    # Check if already loaded
    if collection.count() > 0:
        print(f"Guidelines already loaded: {collection.count()} rules")
        return collection

    # Read guidelines file
    guidelines_path = "data/guidelines/breast_cancer_rules.txt"
    with open(guidelines_path, "r") as f:
        content = f.read()

    # Split into individual rules
    rules = []
    current_rule = []

    for line in content.split("\n"):
        if line.startswith("RULE ") and current_rule:
            rules.append("\n".join(current_rule))
            current_rule = [line]
        elif line.strip():
            current_rule.append(line)

    if current_rule:
        rules.append("\n".join(current_rule))

    # Store each rule with an ID
    for i, rule in enumerate(rules):
        rule_id = f"rule_{i:03d}"
        collection.add(
            documents=[rule],
            ids=[rule_id],
            metadatas=[{"rule_number": i, "source": "breast_cancer_rules.txt"}]
        )
        print(f"Loaded: {rule_id} — {rule[:60]}...")

    print(f"\nTotal rules loaded: {collection.count()}")
    return collection


def query_guidelines(question: str, n_results: int = 3) -> list:
    """
    Query guidelines for relevant rules.
    Returns list of matching rules.
    """
    collection = get_guidelines_store()

    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, collection.count())
    )

    rules = []
    for doc, metadata in zip(
        results["documents"][0],
        results["metadatas"][0]
    ):
        rules.append({
            "rule": doc,
            "rule_number": metadata["rule_number"]
        })

    return rules


if __name__ == "__main__":
    print("Loading guidelines into ChromaDB...")
    load_guidelines_into_store()

    print("\n--- TEST QUERY ---")
    print("Question: What are the rules for comorbidities?")
    results = query_guidelines("comorbidities rules source requirements")

    for r in results:
        print(f"\nRule {r['rule_number']}:")
        print(r["rule"])