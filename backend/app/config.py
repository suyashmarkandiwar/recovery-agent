import os
from dotenv import load_dotenv

load_dotenv(override=True)

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-default-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 5
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

