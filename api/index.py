# backend_admin/api/index.py

import sys
import os

# Add backend_admin/app to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../app"))

from main import app
from mangum import Mangum

handler = Mangum(app)
