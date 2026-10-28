import os
import io
import re
import uuid
import mimetypes
import logging
import urllib.parse
from typing import Union, Optional, Set, Any
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from starlette.datastructures import UploadFile as StarletteUploadFile

UploadFileTypes = (UploadFile, StarletteUploadFile)

import firebase_admin
from firebase_admin import credentials, storage

from app.core.config import settings

# Structured Logger
logger = logging.getLogger("app.core.firebase_storage")


def debugPrint(*args, **kwargs) -> None:
    """
    Safe debug logging utility that mirrors debugPrint behavior.
    Logs formatted messages at DEBUG level to avoid leaking data to raw stdout.
    """
    message = " ".join(str(a) for a in args)
    logger.debug(message)


# Security Limits & Whitelists
MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB default limit
CHUNK_SIZE_BYTES: int = 64 * 1024            # 64 KB chunk size for streaming read

DEFAULT_ALLOWED_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".webp", 
    ".pdf", ".doc", ".docx", 
   ".csv"
}

DANGEROUS_EXTENSIONS: Set[str] = {
    ".exe", ".bat", ".cmd", ".sh", ".php", ".phtml",
    ".py", ".pyc", ".js", ".html", ".htm", ".svg",
    ".jar", ".apk", ".bin", ".dll", ".scr", ".vbs",
    ".cgi", ".pl", ".htaccess", ".config"
}

# Base directory for local fallback storage (sandboxed)
BASE_LOCAL_UPLOAD_DIR: str = os.path.abspath(os.path.join("static", "uploads"))

_firebase_initialized = False
_storage_bucket = None


def sanitize_folder_path(folder_path: str) -> str:
    """
    Sanitizes folder paths to strictly prevent path traversal attacks (e.g. '../', '/').
    Only allows alphanumeric characters, underscores, and hyphens in folder segments.
    """
    if not folder_path:
        return "uploads"

    # Normalize slashes and split
    normalized = folder_path.replace("\\", "/").strip("/")
    segments = normalized.split("/")

    safe_segments = []
    for segment in segments:
        segment = segment.strip().strip(".")
        # Strip all unsafe characters
        cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "", segment)
        if cleaned:
            safe_segments.append(cleaned)

    return "/".join(safe_segments) if safe_segments else "uploads"


def sanitize_filename(filename: str, fallback_ext: str = ".jpg") -> str:
    """
    Sanitizes filename, strips path components, and verifies safety against traversal.
    """
    if not filename:
        return f"file_{uuid.uuid4().hex[:8]}{fallback_ext}"

    # Strip any directory path components
    base_name = os.path.basename(filename)

    # Separate stem and extension
    stem, ext = os.path.splitext(base_name)
    ext = ext.lower().strip()

    # Clean stem
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", stem).strip("._")
    if not clean_stem:
        clean_stem = f"file_{uuid.uuid4().hex[:8]}"
    elif len(clean_stem) > 40:
        clean_stem = clean_stem[:40]

    if not ext:
        ext = fallback_ext

    return f"{clean_stem}{ext}"


def is_path_inside_dir(target_path: str, base_dir: str) -> bool:
    """
    Verifies that target_path strictly resolves inside base_dir to prevent path traversal.
    """
    try:
        target_abs = os.path.abspath(target_path)
        base_abs = os.path.abspath(base_dir)
        return os.path.commonpath([target_abs, base_abs]) == base_abs
    except Exception:
        return False


def get_firebase_bucket():
    """
    Initializes and returns the Firebase Storage bucket singleton.
    If the service account JSON is not found, returns None (allowing safe local fallback).
    """
    global _firebase_initialized, _storage_bucket

    if _storage_bucket is not None:
        return _storage_bucket

    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    bucket_name = settings.FIREBASE_STORAGE_BUCKET

    try:
        if not firebase_admin._apps:
            # Check multiple potential credential locations securely
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            candidate_paths = [
                cred_path,
                os.path.join(base_dir, cred_path) if cred_path else None,
                os.path.join(base_dir, "firebase_service_account.json"),
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            ]

            cred = None
            resolved_source = None
            for path in candidate_paths:
                if path and os.path.exists(path) and os.path.isfile(path):
                    resolved_source = os.path.basename(path)
                    cred = credentials.Certificate(path)
                    break

            if not cred and os.environ.get("FIREBASE_CREDENTIALS_JSON"):
                import json
                try:
                    cred_dict = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
                    cred = credentials.Certificate(cred_dict)
                    resolved_source = "FIREBASE_CREDENTIALS_JSON (env)"
                except Exception as json_err:
                    logger.error(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {json_err}")

            if cred:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
                debugPrint(f"Firebase Admin initialized successfully with bucket: {bucket_name} using {resolved_source}")
                logger.info("Firebase Admin initialized successfully with storage bucket.")
            else:
                logger.warning(
                    f"Firebase credentials not found. Safe local fallback will be used."
                )
                return None

        _storage_bucket = storage.bucket(bucket_name)
        _firebase_initialized = True
        return _storage_bucket

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Storage bucket: {e}")
        return None


def read_file_safely(
    file_data: Union[UploadFile, StarletteUploadFile, bytes, io.BytesIO, Any],
    max_size_bytes: int = MAX_FILE_SIZE_BYTES
) -> bytes:
    """
    Reads file content with strict size enforcement to prevent Memory Exhaustion DoS attacks.
    Supports FastAPI/Starlette UploadFile, BytesIO, bytes, and any file-like objects.
    """
    if file_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided for upload."
        )

    # 1. FastAPI / Starlette UploadFile or object wrapping an underlying file
    if isinstance(file_data, UploadFileTypes) or hasattr(file_data, "file"):
        underlying = getattr(file_data, "file", file_data)
        file_size = getattr(file_data, "size", None)
        if file_size and file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB."
            )

        if hasattr(underlying, "seek"):
            underlying.seek(0)
        buffer = bytearray()
        total_read = 0

        while True:
            chunk = underlying.read(CHUNK_SIZE_BYTES)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB."
                )
            buffer.extend(chunk)

        if hasattr(underlying, "seek"):
            underlying.seek(0)
        return bytes(buffer)

    elif isinstance(file_data, io.BytesIO) or (hasattr(file_data, "getvalue") and hasattr(file_data, "seek")):
        file_data.seek(0)
        content = file_data.getvalue()
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB."
            )
        return content

    elif isinstance(file_data, (bytes, bytearray)):
        if len(file_data) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB."
            )
        return bytes(file_data)

    elif hasattr(file_data, "read"):
        if hasattr(file_data, "seek"):
            file_data.seek(0)
        buffer = bytearray()
        total_read = 0
        while True:
            chunk = file_data.read(CHUNK_SIZE_BYTES)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB."
                )
            buffer.extend(chunk)
        if hasattr(file_data, "seek"):
            file_data.seek(0)
        return bytes(buffer)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format for upload."
        )


def upload_to_firebase(
    file_data: Union[UploadFile, StarletteUploadFile, bytes, io.BytesIO, Any],
    folder_path: str,
    custom_filename: Optional[str] = None,
    content_type: Optional[str] = None,
    allowed_extensions: Optional[Set[str]] = None,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES
) -> str:
    """
    Securely uploads a file to Firebase Storage (or sandboxed local fallback).
    Enforces path traversal protection, file extension whitelisting, and strict size validation.

    Returns:
        Firebase Storage Download URL (or sandboxed local path if Firebase is unavailable).
    """
    # 1. Sanitize folder path
    safe_folder = sanitize_folder_path(folder_path)

    # 2. Extract and sanitize file extension & filename
    original_filename = ""
    if isinstance(file_data, UploadFileTypes) or hasattr(file_data, "filename"):
        original_filename = getattr(file_data, "filename", None) or "file"
        if not content_type and getattr(file_data, "content_type", None):
            content_type = file_data.content_type

    detected_ext = os.path.splitext(original_filename)[1].lower() if original_filename else ".jpg"
    if not detected_ext:
        detected_ext = ".jpg"

    # Validate against allowed extensions
    effective_allowed = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
    if detected_ext in DANGEROUS_EXTENSIONS or detected_ext not in effective_allowed:
        logger.warning(f"Rejected upload with unauthorized extension: '{detected_ext}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{detected_ext}' is not permitted. Allowed: {', '.join(sorted(effective_allowed))}"
        )

    # Determine unique sanitized filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    rand_id = uuid.uuid4().hex[:8]

    if custom_filename:
        # Sanitize custom filename
        safe_custom = sanitize_filename(custom_filename, fallback_ext=detected_ext)
        if not safe_custom.lower().endswith(detected_ext):
            filename = f"{os.path.splitext(safe_custom)[0]}_{rand_id}{detected_ext}"
        else:
            filename = safe_custom
    else:
        safe_stem = sanitize_filename(original_filename, fallback_ext=detected_ext)
        stem_no_ext = os.path.splitext(safe_stem)[0][:25]
        filename = f"{stem_no_ext}_{timestamp}_{rand_id}{detected_ext}"

    # 3. Read content safely with strict size guard
    file_bytes = read_file_safely(file_data, max_size_bytes=max_size_bytes)

    # Guess or validate MIME type
    if not content_type or content_type == "application/octet-stream":
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # Block execution MIME types
    if content_type in {"text/html", "application/javascript", "application/x-httpd-php", "image/svg+xml"}:
        content_type = "application/octet-stream"

    blob_path = f"{safe_folder}/{filename}"
    bucket = get_firebase_bucket()

    # 4. Upload to Firebase Storage
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            download_token = uuid.uuid4().hex
            blob.metadata = {
                "firebaseStorageDownloadTokens": download_token,
                "sanitizedFilename": filename
            }

            # Set Content-Disposition to inline or attachment for security
            content_disposition = f'inline; filename="{filename}"'

            blob.upload_from_string(
                file_bytes,
                content_type=content_type
            )
            blob.content_disposition = content_disposition
            blob.patch()

            try:
                blob.patch()
            except Exception as patch_err:
                logger.warning(f"Failed to patch blob metadata for {blob_path}: {patch_err}")

            try:
                blob.make_public()
            except Exception:
                # Handled safely via download token if Uniform Bucket-Level Access is enforced
                pass

            encoded_path = urllib.parse.quote(blob_path, safe="")
            download_url = (
                f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}"
                f"?alt=media&token={download_token}"
            )
            debugPrint(f"Uploaded file to Firebase Storage blob: {blob_path}")
            logger.info(f"Successfully uploaded file to Firebase Storage: {blob_path}")
            return download_url

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading to Firebase Storage ({blob_path}): {e}. Falling back to safe local storage.")

    # 5. Sandboxed Local Storage Fallback
    target_dir = os.path.abspath(os.path.join(BASE_LOCAL_UPLOAD_DIR, safe_folder))
    if not is_path_inside_dir(target_dir, BASE_LOCAL_UPLOAD_DIR):
        logger.error(f"Path traversal detected in local upload directory resolution: {target_dir}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload directory path."
        )

    os.makedirs(target_dir, exist_ok=True)
    local_file_path = os.path.abspath(os.path.join(target_dir, filename))

    if not is_path_inside_dir(local_file_path, BASE_LOCAL_UPLOAD_DIR):
        logger.error(f"Path traversal detected in local file resolution: {local_file_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename or path."
        )

    try:
        with open(local_file_path, "wb") as f:
            f.write(file_bytes)

        rel_path = os.path.relpath(local_file_path, os.getcwd())
        debugPrint(f"Saved file to local storage fallback: {rel_path}")
        logger.warning(f"File saved to local storage fallback: {rel_path}")
        return f"/{rel_path.replace(os.sep, '/')}"

    except Exception as err:
        logger.error(f"Failed to save file to local storage fallback: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file."
        )


def delete_from_firebase(file_url_or_path: Optional[str]) -> bool:
    """
    Safely deletes a file from Firebase Storage or sandboxed local storage.
    Strictly prevents local path traversal deletions outside of the uploads directory.
    """
    if not file_url_or_path or not isinstance(file_url_or_path, str):
        return False

    # Check if Firebase Storage URL
    if "firebasestorage.googleapis.com" in file_url_or_path:
        bucket = get_firebase_bucket()
        if not bucket:
            return False
        try:
            parsed = urllib.parse.urlparse(file_url_or_path)
            path_part = parsed.path.split("/o/")[-1]
            blob_path = urllib.parse.unquote(path_part)

            # Prevent directory traversal in blob path
            clean_blob_path = blob_path.strip("/")
            if ".." in clean_blob_path:
                logger.warning(f"Blocked suspicious blob path deletion: {blob_path}")
                return False

            blob = bucket.blob(clean_blob_path)
            if blob.exists():
                blob.delete()
                debugPrint(f"Deleted Firebase Storage blob: {clean_blob_path}")
                logger.info(f"Deleted Firebase Storage blob: {clean_blob_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete Firebase Storage blob ({file_url_or_path}): {e}")
            return False

    # Sandboxed local path deletion
    try:
        clean_path = file_url_or_path.lstrip("/").replace("\\", "/")
        target_abs = os.path.abspath(clean_path)

        # STRICT SECURITY CHECK: Must be inside BASE_LOCAL_UPLOAD_DIR
        if not is_path_inside_dir(target_abs, BASE_LOCAL_UPLOAD_DIR):
            logger.warning(f"Security Alert: Blocked unauthorized local file deletion attempt: {target_abs}")
            return False

        if os.path.exists(target_abs) and os.path.isfile(target_abs):
            os.remove(target_abs)
            debugPrint(f"Deleted local file: {target_abs}")
            logger.info(f"Deleted sandboxed local file: {target_abs}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete local file ({file_url_or_path}): {e}")
        return False

    return False
