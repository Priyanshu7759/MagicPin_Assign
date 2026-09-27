import time
import requests
from fastapi.testclient import TestClient
from bot import app

client = TestClient(app)

def test_endpoints():
    # 1. Healthz
    res = client.get("/v1/healthz")
    assert res.status_code == 200
    print("Healthz:", res.json())
    
    # 2. Metadata
    res = client.get("/v1/metadata")
    assert res.status_code == 200
    print("Metadata:", res.json())
    
    # 3. Push Context
    res = client.post("/v1/context", json={
        "scope": "category",
        "context_id": "dentists",
        "version": 1,
        "payload": {"slug": "dentists", "voice": {"tone": "clinical_peer"}}
    })
    assert res.status_code == 200
    print("Push Category:", res.json())
    
    res = client.post("/v1/context", json={
        "scope": "merchant",
        "context_id": "m_001_drmeera",
        "version": 1,
        "payload": {
            "merchant_id": "m_001_drmeera",
            "category_slug": "dentists",
            "identity": {"name": "Dr Meera's Dental Clinic", "owner_first_name": "Meera", "locality": "Lajpat Nagar"},
            "performance": {"views": 2410, "calls": 18, "ctr": 0.021},
            "offers": [{"title": "Dental Cleaning @ ₹299", "status": "active"}]
        }
    })
    assert res.status_code == 200
    print("Push Merchant:", res.json())

    # 4. Push Trigger
    res = client.post("/v1/context", json={
        "scope": "trigger",
        "context_id": "trg_001",
        "version": 1,
        "payload": {
            "id": "trg_001",
            "kind": "research_digest",
            "scope": "merchant",
            "merchant_id": "m_001_drmeera"
        }
    })
    assert res.status_code == 200
    
    # Check Healthz again
    res = client.get("/v1/healthz")
    print("Healthz loaded:", res.json()["contexts_loaded"])

    # 5. Tick
    res = client.post("/v1/tick", json={
        "now": "2026-04-26T10:00:00Z",
        "available_triggers": ["trg_001"]
    })
    assert res.status_code == 200
    print("Tick response:", res.json())

    # 6. Reply (Auto-reply)
    res = client.post("/v1/reply", json={
        "conversation_id": "conv_001",
        "from_role": "merchant",
        "message": "Thank you for contacting us! Our team will respond shortly.",
        "turn_number": 2
    })
    assert res.status_code == 200
    print("Reply (Auto-reply):", res.json())

    # 7. Reply (Intent commitment)
    res = client.post("/v1/reply", json={
        "conversation_id": "conv_002",
        "from_role": "merchant",
        "message": "Ok lets do it. Whats next?",
        "turn_number": 2
    })
    assert res.status_code == 200
    print("Reply (Intent):", res.json())

    print("\nALL ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
