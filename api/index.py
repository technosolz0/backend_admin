import sys
import os

# Add path to app folder
sys.path.append(os.path.join(os.path.dirname(__file__), "../app"))

# Import FastAPI app
from app.main import app

# Mangum to wrap FastAPI for AWS Lambda / Vercel
from mangum import Mangum

# 👇 This is critical for Vercel
handler = Mangum(app)
