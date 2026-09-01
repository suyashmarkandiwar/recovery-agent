from fastapi import APIRouter
from app.scheduler import process_overdue_invoices
from app.db.database import get_session
from app.db.models import Invoice, AuditLog
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from app.integrations.sendgrid_client import send_email
import json

router = APIRouter()

@router.post("/run-recovery")
def trigger_recovery():
    process_overdue_invoices()
    return {"status": "success", "message": "Recovery process triggered!"}


@router.post("/{invoice_id}/resend-link")
async def resend_payment_link(invoice_id: int, session: Session = Depends(get_session)):
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status == "PAID":
        return {"message": "Invoice is already paid."}

    # 1. Log the manual action
    assert invoice.id is not None
    audit = AuditLog(
        invoice_id=invoice.id,
        event_type="manual_resend",
        payload=json.dumps({"action": "Manual link resend triggered"})
    )
    session.add(audit)
    session.commit()

    # 2. Trigger your SendGrid email
    subject = f"Payment Reminder for Invoice #{invoice.id}"
    body = f"Please pay your outstanding balance using this link: {invoice.razorpay_short_url}"
    send_email(to_email=invoice.client_email, subject=subject, body=body)

    return {"status": "success", "message": f"Payment link manually resent for Invoice #{invoice_id}"}