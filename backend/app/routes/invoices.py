from fastapi import APIRouter
from app.scheduler import process_overdue_invoices
from app.db.database import get_session
from app.db.models import Invoice, AuditLog
from sqlmodel import Session, select
from fastapi import HTTPException, Depends
from app.integrations.sendgrid_client import send_email
from app.security import get_current_user
import json
from datetime import date  
from pydantic import BaseModel  
from typing import Literal

router = APIRouter(dependencies=[Depends(get_current_user)])

class NegotiatedDateRequest(BaseModel):
    proposed_date: date

class WriteOffRequest(BaseModel):
    outcome: Literal["BAD_DEBT", "LEGAL", "OVERDUE"]

@router.post("/run-recovery")
def trigger_recovery():
    process_overdue_invoices()
    return {"status": "success", "message": "Recovery process triggered!"}

@router.get("/")
def get_invoices(session: Session = Depends(get_session)):
    invoices = session.exec(select(Invoice)).all()
    today = date.today()
    results = []
    for inv in invoices:
        data = inv.model_dump()
        data["days_passed"] = (today - inv.due_date).days
        results.append(data)
    return {"status": "success", "data": results}


@router.post("/{invoice_id}/resend-link")
async def resend_payment_link(invoice_id: int, session: Session = Depends(get_session)):
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status == "PAID":
        return {"message": "Invoice is already paid."}

    # 1. Clear requires_call + log the action
    invoice.requires_call = False
    assert invoice.id is not None
    audit = AuditLog(
        invoice_id=invoice.id,
        event_type="manual_resend",
        payload=json.dumps({"action": "Payment link resent. requires_call cleared. Awaiting Razorpay webhook for PAID status."})
    )
    session.add(invoice)
    session.add(audit)
    session.commit()

    # If no payment link exists yet, create one on the fly
    if not invoice.razorpay_short_url:
        from app.integrations.razorpay_client import create_payment_link
        link_id, short_url = create_payment_link(invoice.id, invoice.amount, invoice.client_name, invoice.client_email)
        if not short_url:
            raise HTTPException(status_code=500, detail="Failed to generate a Razorpay payment link. Try again.")
        invoice.razorpay_link_id = link_id
        invoice.razorpay_short_url = short_url
        session.add(invoice)
        session.commit()

    # 2. Send payment link via email
    subject = f"Payment Reminder for Invoice #{invoice.id}"
    body = f"Please pay your outstanding balance using this link: {invoice.razorpay_short_url}"
    email_sent = send_email(to_email=invoice.client_email, subject=subject, body=body)

    if not email_sent:
        raise HTTPException(status_code=502, detail="Payment link saved but email dispatch failed. Try again.")

    return {"status": "success", "message": f"Payment link resent for Invoice #{invoice_id}"}

@router.patch("/{invoice_id}/negotiated-date")
def set_negotiated_date(
    invoice_id: int,
    body: NegotiatedDateRequest,
    session: Session = Depends(get_session)
):
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    proposed_date = body.proposed_date
    today = date.today()
    delta_days = (proposed_date - invoice.due_date).days
    # Server-side re-validation of the 30-day cap
    if proposed_date < today or delta_days > 30:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date: {'past date' if proposed_date < today else 'exceeds 30-day cap'}"
        )
    invoice.pause_followups_until = proposed_date
    invoice.requires_call = False
    assert invoice.id is not None
    audit = AuditLog(
        invoice_id=invoice.id,
        event_type="negotiated_date_set",
        payload=json.dumps({
            "proposed_date": str(proposed_date),
            "due_date": str(invoice.due_date),
            "delta_days": delta_days
        })
    )
    session.add(invoice)
    session.add(audit)
    session.commit()
    return {"status": "success", "pause_followups_until": str(proposed_date)}

@router.patch("/{invoice_id}/write-off")
def write_off_invoice(
    invoice_id: int,
    body: WriteOffRequest,
    session: Session = Depends(get_session)
):
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "PAID":
        raise HTTPException(status_code=400, detail="Cannot change status of a PAID invoice")
    previous_status = invoice.status
    invoice.status = body.outcome
    invoice.requires_call = False
    assert invoice.id is not None
    audit = AuditLog(
        invoice_id=invoice.id,
        event_type="invoice_written_off",
        payload=json.dumps({
            "outcome": body.outcome,
            "previous_status": previous_status,
            "reason": "Customer refused or unreachable"
        })
    )
    session.add(invoice)
    session.add(audit)
    session.commit()
    return {"status": "success", "invoice_status": body.outcome}