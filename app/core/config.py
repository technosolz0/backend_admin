import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OTPConfig:
    EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 3
    MAX_RESENDS = 3
    RESEND_COOLDOWN_MINUTES = 1

class Settings:
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET")

settings = Settings()