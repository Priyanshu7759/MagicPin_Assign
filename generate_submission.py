"""
magicpin AI Challenge — Submission Generator
============================================
Generates 30-line submission.jsonl from expanded canonical test pairs.
"""

import os
import json
from pathlib import Path
import composer

EXPANDED_DIR = Path("expanded")

def load_json_file(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generate():
    # 1. Load test pairs
    test_pairs_path = EXPANDED_DIR / "test_pairs.json"
    if not test_pairs_path.exists():
        raise FileNotFoundError("expanded/test_pairs.json not found! Run generate_dataset.py first.")
        
    test_pairs_data = load_json_file(test_pairs_path)
    pairs = test_pairs_data.get("pairs", [])
    
    # 2. Load Categories
    categories = {}
    cat_dir = EXPANDED_DIR / "categories"
    if cat_dir.exists():
        for p in cat_dir.glob("*.json"):
            data = load_json_file(p)
            slug = data.get("slug")
            if slug:
                categories[slug] = data
                
    # 3. Load Merchants
    merchants = {}
    m_dir = EXPANDED_DIR / "merchants"
    if m_dir.exists():
        for p in m_dir.glob("*.json"):
            data = load_json_file(p)
            mid = data.get("merchant_id")
            if mid:
                merchants[mid] = data

    # 4. Load Triggers
    triggers = {}
    t_dir = EXPANDED_DIR / "triggers"
    if t_dir.exists():
        for p in t_dir.glob("*.json"):
            data = load_json_file(p)
            tid = data.get("id")
            if tid:
                triggers[tid] = data

    # 5. Load Customers
    customers = {}
    c_dir = EXPANDED_DIR / "customers"
    if c_dir.exists():
        for p in c_dir.glob("*.json"):
            data = load_json_file(p)
            cid = data.get("customer_id")
            if cid:
                customers[cid] = data

    submission_lines = []
    
    for item in pairs:
        test_id = item.get("test_id")
        merchant_id = item.get("merchant_id")
        trigger_id = item.get("trigger_id")
        customer_id = item.get("customer_id")
        
        merchant = merchants.get(merchant_id, {})
        cat_slug = merchant.get("category_slug", "dentists")
        category = categories.get(cat_slug, {"slug": cat_slug})
        trigger = triggers.get(trigger_id, {"id": trigger_id, "kind": "generic", "scope": "merchant"})
        customer = customers.get(customer_id) if customer_id else None
        
        composed = composer.compose(category, merchant, trigger, customer)
        
        entry = {
            "test_id": test_id,
            "body": composed["body"],
            "cta": composed["cta"],
            "send_as": composed["send_as"],
            "suppression_key": composed["suppression_key"],
            "rationale": composed["rationale"]
        }
        submission_lines.append(entry)

    out_path = Path("submission.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for line in submission_lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    print(f"Successfully generated submission.jsonl with {len(submission_lines)} lines!")

if __name__ == "__main__":
    generate()
