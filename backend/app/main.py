import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.scheduler import scheduler
from app.routes import auth, invoices, razorpay_webhook, sendgrid_inbound, analytics
from sqlmodel import select, Session
from app.db.database import engine, create_db_and_tables
from app.db.models import Employee
from app.security import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist in the database
    create_db_and_tables()
    
    # Auto-create default admin employee on startup
    db = Session(engine)
    try:
        statement = select(Employee).where(Employee.username == "admin")
        admin_user = db.exec(statement).first()
        if not admin_user:
            print("Creating default admin employee...")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            hashed_password = get_password_hash(admin_password)
            new_admin = Employee(username="admin", hashed_password=hashed_password)
            db.add(new_admin)
            db.commit()
            print("Default admin created successfully!")
    except Exception as e:
        print(f"Error auto-creating admin: {e}")
    finally:
        db.close()

    scheduler.start()
    yield
    scheduler.shutdown()
    
app = FastAPI(title="Recovery Agent API", lifespan=lifespan)

# Setup CORS to allow your React frontend to attach cookies
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "https://recovery-agent-theta.vercel.app", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(razorpay_webhook.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(sendgrid_inbound.router, prefix="/api/email", tags=["Email"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])