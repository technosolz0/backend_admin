import os
import io
import uuid
import mimetypes
import logging
import urllib.parse
from typing import Union, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException

import firebase_admin
from firebase_admin import credentials, storage

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_initialized = False
_storage_bucket = None


def get_firebase_bucket():
    """
    Initializes and returns the Firebase Storage bucket.
    If the service account JSON is not found, returns None (allowing local fallback).
    """
    global _firebase_initialized, _storage_bucket

    if _storage_bucket is not None:
        return _storage_bucket

    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    bucket_name = settings.FIREBASE_STORAGE_BUCKET

    try:
        if not firebase_admin._apps:
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
                logger.info(f"Firebase Admin initialized successfully with bucket: {bucket_name}")
            else:
                logger.warning(
                    f"Firebase credentials file not found at '{cred_path}'. "
                    "Uploads will fallback to local storage until credentials are provided."
                )
                return None
        
        _storage_bucket = storage.bucket(bucket_name)
        _firebase_initialized = True
        return _storage_bucket

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Storage bucket '{bucket_name}': {e}")
        return None


def upload_to_firebase(
    file_data: Union[UploadFile, bytes, io.BytesIO],
    folder_path: str,
    custom_filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Uploads a file to Firebase Storage under the given folder path.
    Example folder_path: 'vendors/12/documents/bank' or 'categories/5'
    
    Returns:
        Firebase Storage Download URL (or local file path if Firebase is not configured).
    """
    bucket = get_firebase_bucket()

    # 1. Determine original filename and extension
    original_filename = ""
    if isinstance(file_data, UploadFile):
        original_filename = file_data.filename or "file"
        if not content_type and file_data.content_type:
            content_type = file_data.content_type
    
    ext = os.path.splitext(original_filename)[1].lower() if original_filename else ".jpg"

    # 2. Determine unique filename
    if custom_filename:
        filename = custom_filename if "." in custom_filename else f"{custom_filename}{ext}"
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rand_id = uuid.uuid4().hex[:8]
        clean_name = os.path.splitext(original_filename)[0][:20] if original_filename else "file"
        filename = f"{clean_name}_{timestamp}_{rand_id}{ext}"

    # Clean destination path
    folder_clean = folder_path.strip("/")
    blob_path = f"{folder_clean}/{filename}"

    if not content_type:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # 3. Upload to Firebase Storage if available
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            download_token = str(uuid.uuid4())
            blob.metadata = {"firebaseStorageDownloadTokens": download_token}

            if isinstance(file_data, UploadFile):
                file_data.file.seek(0)
                blob.upload_from_file(file_data.file, content_type=content_type)
            elif isinstance(file_data, io.BytesIO):
                file_data.seek(0)
                blob.upload_from_file(file_data, content_type=content_type)
            elif isinstance(file_data, bytes):
                blob.upload_from_string(file_data, content_type=content_type)
            else:
                raise ValueError(f"Unsupported file_data type: {type(file_data)}")

            try:
                blob.make_public()
            except Exception:
                # In case Uniform Bucket Access is active, download token handles access
                pass

            # Standard Firebase Storage direct download URL
            encoded_path = urllib.parse.quote(blob_path, safe="")
            download_url = (
                f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}"
                f"?alt=media&token={download_token}"
            )
            logger.info(f"Uploaded file to Firebase Storage: {blob_path}")
            return download_url

        except Exception as e:
            logger.error(f"Error uploading to Firebase Storage ({blob_path}): {e}. Falling back to local storage.")

    # 4. Fallback: Local file saving
    local_dir = os.path.join("static", "uploads", folder_clean)
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, filename)

    try:
        with open(local_path, "wb") as buffer:
            if isinstance(file_data, UploadFile):
                file_data.file.seek(0)
                buffer.write(file_data.file.read())
            elif isinstance(file_data, io.BytesIO):
                file_data.seek(0)
                buffer.write(file_data.getvalue())
            elif isinstance(file_data, bytes):
                buffer.write(file_data)

        logger.warning(f"File saved locally as fallback: {local_path}")
        return f"/{local_path}"
    except Exception as local_err:
        logger.error(f"Failed to save file locally: {local_err}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


def delete_from_firebase(file_url_or_path: Optional[str]) -> bool:
    """
    Deletes a file from Firebase Storage or local disk if it exists.
    """
    if not file_url_or_path:
        return False

    # Check if Firebase Storage URL
    if "firebasestorage.googleapis.com" in file_url_or_path:
        bucket = get_firebase_bucket()
        if not bucket:
            return False
        try:
            # Parse path from URL
            # Format: https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_path}?alt=media...
            parsed = urllib.parse.urlparse(file_url_or_path)
            path_part = parsed.path.split("/o/")[-1]
            blob_path = urllib.parse.unquote(path_part)
            blob = bucket.blob(blob_path)
            if blob.exists():
                blob.delete()
                logger.info(f"Deleted Firebase Storage blob: {blob_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete Firebase Storage file ({file_url_or_path}): {e}")
            return False

    # Otherwise treat as local path
    try:
        clean_path = file_url_or_path.lstrip("/")
        if os.path.exists(clean_path):
            os.remove(clean_path)
            logger.info(f"Deleted local file: {clean_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete local file ({file_url_or_path}): {e}")

    return False
