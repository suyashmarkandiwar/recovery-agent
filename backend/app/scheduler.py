from datetime import date, datetime, timezone
from sqlmodel import Session, select, or_, col
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.database import engine
from app.db.models import Invoice, AuditLog
from app.agent.tone_logic import determine_tone
from app.agent.orchestrator import draft_recovery_email
from app.integrations.sendgrid_client import send_email
from app.integrations.razorpay_client import create_payment_link


def process_overdue_invoices():
    with Session(engine) as session:
        today = date.today()
        
        # 3.2 Query overdue, not escalated, and not paused
        query = select(Invoice).where(
            Invoice.status == "OVERDUE",
            col(Invoice.requires_call).is_(False),
            or_(Invoice.pause_followups_until == None, col(Invoice.pause_followups_until) < today)
        ).order_by(col(Invoice.id)) # <-- Added this
        invoices = session.exec(query).all()

        for invoice in invoices:
            days_passed = (today - invoice.due_date).days
            tone = determine_tone(days_passed)

            if tone is None:
                continue  # Skip 0-10 days
            
            if tone == "ESCALATE":
                invoice.requires_call = True
                assert invoice.id is not None
                session.add(AuditLog(invoice_id=invoice.id, event_type="auto_escalated", timestamp=datetime.now(timezone.utc)))
                session.commit()
                continue
            
            # 3.3 4-Day Cooldown Check
            if invoice.last_contacted and (today - invoice.last_contacted).days < 4:
                continue

            # Target identified! We will inject Groq and SendGrid here next.
            # 3.4 Groq Call
            assert invoice.id is not None
            draft = draft_recovery_email(invoice.client_name, invoice.amount, invoice.id, tone, days_passed)
            
            if "error" in draft:
                print(f"AI Error for Invoice {invoice.id}: {draft.get('raw')}")
                continue

            # 3.5 Validation & Link Injection (Using mock Razorpay link for now)
            actual_link = invoice.razorpay_short_url

            # If there is no existing link, generate a new real one
            if not actual_link:
                link_id, short_url = create_payment_link(invoice.id, invoice.amount, invoice.client_name, invoice.client_email)
                if short_url:
                    actual_link = short_url
                    invoice.razorpay_link_id = link_id
                    invoice.razorpay_short_url = short_url
                    session.add(invoice)
                    session.commit()
            
            if not actual_link:
                print(f"Failed to generate/inject link for Invoice {invoice.id}")
                continue

            final_body = draft["email_body"].replace("{PAYMENT_LINK}", actual_link)
            
            if actual_link not in final_body:
                print(f"Failed to inject link for Invoice {invoice.id}")
                continue

            # 3.6 & 3.7 Dispatch and Audit
            final_subject = f"{draft['email_subject']} [Invoice #{invoice.id}]"
            
            
            if send_email(invoice.client_email, final_subject, final_body):
                invoice.last_contacted = today
                assert invoice.id is not None  # Add this to satisfy the type checker
                session.add(AuditLog(invoice_id=invoice.id, event_type="email_sent", timestamp=datetime.now(timezone.utc)))
                session.commit()
                print(f"Successfully sent {tone} email to {invoice.client_name}!")
                
        # Record batch completion
        session.add(AuditLog(event_type="batch_scan_completed", payload="Recovery agent finished scanning overdue invoices.", timestamp=datetime.now(timezone.utc)))
        session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(process_overdue_invoices, 'cron', hour=8, minute=0) # Temporarily set to 18:46 for testing
