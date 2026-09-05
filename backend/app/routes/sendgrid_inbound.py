# app/routes/sendgrid_inbound.py

import re
import json
from fastapi import APIRouter, Request, Depends
from sqlmodel import Session
from app.db.database import get_session
from app.db.models import Invoice, AuditLog
from app.integrations.groq_client import generate_message
from datetime import date

router = APIRouter()


def extract_invoice_id(subject: str) -> int | None:
    match = re.search(r"Invoice\s*#(\d+)", subject, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_date_from_body(body: str) -> str | None:
    prompt = f"""You are a date extraction assistant.
Read the following email reply and extract the date the customer is proposing to make their payment.
Return ONLY a date in YYYY-MM-DD format, or return null (the word null, nothing else) if no clear date is mentioned.
Do not explain. Do not add any other text.

Email:
\"\"\"
{body}
\"\"\"
"""
    raw = generate_message(prompt).strip()

    # Strip <think> blocks (Qwen/DeepSeek)
    think_end = raw.rfind("</think>")
    raw = raw[think_end + len("</think>"):].strip() if think_end != -1 else raw

    if raw.lower() == "null" or not raw:
        return None

    # Validate format strictly
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw

    return None


@router.post("/inbound")
async def receive_inbound_email(request: Request, session: Session = Depends(get_session)):
    form = await request.form()

    sender     = str(form.get("from", ""))
    subject    = str(form.get("subject", ""))
    body_plain = str(form.get("text", ""))

    # 5.2 — Extract & validate invoice_id from subject
    invoice_id = extract_invoice_id(subject)

    if invoice_id is None:
        audit = AuditLog(
            invoice_id=None,
            event_type="inbound_parse_failed",
            payload=json.dumps({"reason": "missing_invoice_id", "subject": subject, "from": sender})
        )
        session.add(audit)
        session.commit()
        return {"status": "customer_care", "reason": "missing_invoice_id"}

    invoice = session.get(Invoice, invoice_id)

    if invoice is None:
        audit = AuditLog(
            invoice_id=None,
            event_type="inbound_parse_failed",
            payload=json.dumps({"reason": "tampered_invoice_id", "invoice_id": invoice_id, "from": sender})
        )
        session.add(audit)
        session.commit()
        return {"status": "customer_care", "reason": "tampered_invoice_id"}

    # 5.3 — Feed body to Groq, extract structured date
    proposed_date_str = extract_date_from_body(body_plain)

    if proposed_date_str is None:
        audit = AuditLog(
            invoice_id=invoice.id,
            event_type="inbound_vague_reply",
            payload=json.dumps({"reason": "no_valid_date", "from": sender, "body": body_plain[:300]})
        )
        session.add(audit)
        session.commit()
        return {"status": "customer_care", "reason": "no_valid_date"}

    # 5.5 — Validate proposed date
    try:
        proposed_date = date.fromisoformat(proposed_date_str)
    except ValueError:
        audit = AuditLog(
            invoice_id=invoice.id,
            event_type="inbound_vague_reply",
            payload=json.dumps({"reason": "invalid_date_value", "raw_date": proposed_date_str, "from": sender})
        )
        session.add(audit)
        session.commit()
        return {"status": "customer_care", "reason": "invalid_date_value"}

    today = date.today()
    delta_days = (proposed_date - invoice.due_date).days

    if proposed_date < today or delta_days > 30:
        invoice.requires_call = True
        audit = AuditLog(
            invoice_id=invoice.id,
            event_type="inbound_date_rejected",
            payload=json.dumps({
                "proposed_date": proposed_date_str,
                "due_date": str(invoice.due_date),
                "delta_days": delta_days,
                "reason": "past_date" if proposed_date < today else "too_far_out"
            })
        )
        session.add(invoice)
        session.add(audit)
        session.commit()
        return {"status": "requires_call", "proposed_date": proposed_date_str}

    # Valid date — pause follow-ups until proposed date
    invoice.pause_followups_until = proposed_date
    audit = AuditLog(
        invoice_id=invoice.id,
        event_type="inbound_date_accepted",
        payload=json.dumps({
            "proposed_date": proposed_date_str,
            "pause_followups_until": proposed_date_str
        })
    )
    session.add(invoice)
    session.add(audit)
    session.commit()
    return {"status": "accepted", "pause_followups_until": proposed_date_str}
