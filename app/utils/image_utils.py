from PIL import Image
import io
from fastapi import UploadFile

def compress_image(
    upload_file: UploadFile,
    max_size: tuple[int, int] = (500, 500),
    quality: int = 70
) -> bytes:
    image = Image.open(upload_file.file)

    # Convert to RGB if PNG with alpha channel
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Resize dynamically only if larger
    image.thumbnail(max_size)

    # Save to memory with compression
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG", quality=quality, optimize=True)
    img_bytes.seek(0)
    return img_bytes
