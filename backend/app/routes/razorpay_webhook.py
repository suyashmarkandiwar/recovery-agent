import json
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlmodel import Session
from app.db.database import get_session
from app.db.models import Invoice, AuditLog, ProcessedWebhookEvent
from app.config import RAZORPAY_WEBHOOK_SECRET
from app.integrations.razorpay_client import client

router = APIRouter()

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request, 
    x_razorpay_signature: str = Header(None), 
    session: Session = Depends(get_session)
):
    payload = await request.body()
    
    # 1. Verify Signature
    try:
        client.utility.verify_webhook_signature( # type: ignore
            payload.decode('utf-8'), x_razorpay_signature, RAZORPAY_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(payload)
    event_id = request.headers.get("x-razorpay-event-id")
    if event_id is None:
        raise HTTPException(status_code=400, detail="Missing x-razorpay-event-id header")
    event_type = data.get("event")

    # 2. Deduplication check
    if session.get(ProcessedWebhookEvent, event_id):
        return {"status": "already_processed"}

    # 3. Process Payment Event
    if event_type == "payment_link.paid":
        ref_id = data["payload"]["payment_link"]["entity"].get("reference_id")
        
        if ref_id and ref_id.isdigit():
            invoice = session.get(Invoice, int(ref_id))
            if invoice:
                invoice.status = "PAID"
                assert invoice.id is not None
                audit = AuditLog(
                    invoice_id=invoice.id, 
                    event_type="payment_captured", 
                    payload=json.dumps({"event_id": event_id})
                )
                session.add(invoice)
                session.add(audit)

    # 4. Mark Event as Processed
    session.add(ProcessedWebhookEvent(event_id=event_id))
    session.commit()
    
    return {"status": "success"}