import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.scheduler import scheduler
from app.routes import auth, invoices, razorpay_webhook, sendgrid_inbound, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
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



