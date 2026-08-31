 
from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date, datetime, timezone

class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str
    client_email: str
    client_phone: Optional[str] = None
    amount: float
    due_date: date
    last_contacted: Optional[date] = None
    status: str = Field(default="OVERDUE") 
    pause_followups_until: Optional[date] = None
    razorpay_link_id: Optional[str] = None
    razorpay_short_url: Optional[str] = None
    requires_call: bool = Field(default=False)

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str 
    payload: Optional[str] = None 

class ProcessedWebhookEvent(SQLModel, table=True):
    event_id: str = Field(primary_key=True)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))