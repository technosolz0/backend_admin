import os
from fastapi import UploadFile
from uuid import uuid4

UPLOAD_DIR = "uploads"

async def save_upload_file(upload_file: UploadFile, folder: str = ""):
    os.makedirs(os.path.join(UPLOAD_DIR, folder), exist_ok=True)
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, folder, filename)

    with open(file_path, "wb") as f:
        content = await upload_file.read()
        f.write(content)

    return f"/{UPLOAD_DIR}/{folder}/{filename}"
