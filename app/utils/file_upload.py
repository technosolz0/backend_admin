from fastapi import UploadFile
from app.core.firebase_storage import upload_to_firebase

async def save_upload_file(upload_file: UploadFile, folder: str = ""):
    return upload_to_firebase(upload_file, folder_path=folder or "uploads")
