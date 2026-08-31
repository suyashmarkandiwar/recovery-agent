import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-default-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 5
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")
