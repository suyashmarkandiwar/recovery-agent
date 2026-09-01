from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
from app.routes import invoices
from contextlib import asynccontextmanager
from app.scheduler import process_overdue_invoices
from fastapi import APIRouter
from app.scheduler import process_overdue_invoices
from app.routes import razorpay_webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    # scheduler.start()
    yield
    # scheduler.shutdown()

app = FastAPI(title="Recovery Agent API", lifespan=lifespan)

# Setup CORS to allow your React frontend to attach cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])

app.include_router(razorpay_webhook.router, prefix="/api/webhooks", tags=["Webhooks"])

@app.get("/")
def health_check():
    return {"status": "ok"}

