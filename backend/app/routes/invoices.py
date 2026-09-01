from fastapi import APIRouter
from app.scheduler import process_overdue_invoices

router = APIRouter()

@router.post("/run-recovery")
def trigger_recovery():
    process_overdue_invoices()
    return {"status": "success", "message": "Recovery process triggered!"}
