"""
magicpin AI Challenge — Vera Bot Server
=======================================
FastAPI server exposing all 5 required endpoints for the evaluation judge harness:
1. GET /v1/healthz
2. GET /v1/metadata
3. POST /v1/context
4. POST /v1/tick
5. POST /v1/reply
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

import composer

app = FastAPI(title="Vera Bot - magicpin AI Challenge", version="1.0.0")

START_TIME = time.time()

# In-memory store for contexts: (scope, context_id) -> {"version": int, "payload": dict}
contexts: Dict[tuple, Dict[str, Any]] = {}
conversations: Dict[str, List[Dict[str, Any]]] = {}


class ContextPushBody(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: Optional[str] = None


class TickBody(BaseModel):
    now: str
    available_triggers: List[str] = []


class ReplyBody(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: Optional[str] = None
    turn_number: int = 1

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "vera-bot",
        "healthz": "/v1/healthz",
        "metadata": "/v1/metadata"
    }


@app.get("/v1/healthz")
async def healthz():
    """Liveness & Readiness probe checked by judge harness."""
    counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
    for (scope, _), _ in contexts.items():
        if scope in counts:
            counts[scope] += 1

    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "contexts_loaded": counts
    }


@app.get("/v1/metadata")
async def metadata():
    """Bot team & technical identity for leaderboard and evaluation."""
    return {
        "team_name": "Team Vera Precision",
        "team_members": ["Soumya Khandelwal"],
        "model": "rule-guided-deterministic-composer",
        "approach": "4-context grounded composer with multi-turn auto-reply detection & intent transition",
        "contact_email": "soumya@example.com",
        "version": "1.0.0",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }


@app.post("/v1/context")
async def push_context(body: ContextPushBody):
    """Stores context pushed by judge harness. Idempotent by (scope, context_id, version)."""
    key = (body.scope, body.context_id)
    cur = contexts.get(key)
    
    if cur and cur["version"] > body.version:
        return {
            "accepted": False,
            "reason": "stale_version",
            "current_version": cur["version"]
        }
        
    contexts[key] = {
        "version": body.version,
        "payload": body.payload
    }
    
    return {
        "accepted": True,
        "ack_id": f"ack_{body.context_id}_v{body.version}",
        "stored_at": datetime.now(timezone.utc).isoformat()
    }


@app.post("/v1/tick")
async def tick(body: TickBody):
    """Periodic tick wake-up. Bot evaluates active triggers and composes actions."""
    actions = []
    
    for trg_id in body.available_triggers:
        trg_ctx = contexts.get(("trigger", trg_id), {}).get("payload")
        if not trg_ctx:
            trg_ctx = {"id": trg_id, "kind": "research_digest", "scope": "merchant"}
            
        merchant_id = trg_ctx.get("merchant_id") or trg_ctx.get("payload", {}).get("merchant_id")
        customer_id = trg_ctx.get("customer_id") or trg_ctx.get("payload", {}).get("customer_id")
        
        merchant = None
        if merchant_id:
            merchant = contexts.get(("merchant", merchant_id), {}).get("payload")
            
        if not merchant:
            for (s, _), data in contexts.items():
                if s == "merchant":
                    merchant = data["payload"]
                    merchant_id = merchant.get("merchant_id")
                    break
                    
        if not merchant:
            continue
            
        cat_slug = merchant.get("category_slug", "dentists")
        category = contexts.get(("category", cat_slug), {}).get("payload", {"slug": cat_slug})
        
        customer = None
        if customer_id:
            customer = contexts.get(("customer", customer_id), {}).get("payload")
            
        composed = composer.compose(category, merchant, trg_ctx, customer)
        
        conv_id = f"conv_{merchant_id}_{trg_id}"
        actions.append({
            "conversation_id": conv_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "send_as": composed["send_as"],
            "trigger_id": trg_id,
            "template_name": "vera_custom_v1",
            "template_params": [merchant.get("identity", {}).get("name", ""), "...", "..."],
            "body": composed["body"],
            "cta": composed["cta"],
            "suppression_key": composed["suppression_key"],
            "rationale": composed["rationale"]
        })
        
    return {"actions": actions}


@app.post("/v1/reply")
async def reply(body: ReplyBody):
    """Processes replies from simulated merchant/customer."""
    conversations.setdefault(body.conversation_id, []).append({
        "from": body.from_role,
        "msg": body.message,
        "turn": body.turn_number
    })
    
    resp = composer.respond_to_reply(
        conversation_id=body.conversation_id,
        merchant_id=body.merchant_id or "",
        from_role=body.from_role,
        message=body.message,
        turn_number=body.turn_number
    )
    
    return resp


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
