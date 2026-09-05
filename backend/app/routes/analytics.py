from fastapi import APIRouter, Depends
from sqlmodel import Session, select, col
from sqlalchemy import func
from app.db.database import get_session
from app.db.models import Invoice, AuditLog
from app.security import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/recovery-stats")
def get_recovery_stats(session: Session = Depends(get_session)):
    # 1. Total Money Recovered (PAID)
    recovered = session.exec(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(Invoice.status == "PAID")
    ).first()

    # 2. Total Money Currently At Risk / Overdue
    overdue = session.exec(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(Invoice.status == "OVERDUE")
    ).first()

    # 3. Total Money Written Off (BAD_DEBT or LEGAL)
    written_off = session.exec(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(col(Invoice.status).in_(["BAD_DEBT", "LEGAL"]))
    ).first()

    # Counts
    recovered_count = session.exec(select(func.count(col(Invoice.id))).where(Invoice.status == "PAID")).first()
    overdue_count = session.exec(select(func.count(col(Invoice.id))).where(Invoice.status == "OVERDUE")).first()

    return {
        "status": "success",
        "data": {
            "financials": {
                "total_recovered": float(recovered or 0),
                "total_at_risk": float(overdue or 0),
                "total_written_off": float(written_off or 0)
            },
            "counts": {
                "paid_invoices": recovered_count,
                "active_overdue_invoices": overdue_count
            }
        }
    }

@router.get("/last-scan-time")
def get_last_scan_time(session: Session = Depends(get_session)):
    log = session.exec(
        select(AuditLog)
        .where(AuditLog.event_type == "batch_scan_completed")
        .order_by(col(AuditLog.timestamp).desc())
    ).first()
    return {
        "status": "success", 
        "last_scan_time": log.timestamp.isoformat() if log else None
    }
