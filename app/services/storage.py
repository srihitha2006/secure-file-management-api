import os
import uuid
import aiofiles
from fastapi import UploadFile

from app.core.config import settings

CHUNK_SIZE = 1024 * 1024  # 1 MB

def ensure_storage_dir():
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)

def build_path(stored_name: str) -> str:
    return os.path.join(settings.STORAGE_DIR, stored_name)

async def save_upload_file(file: UploadFile) -> tuple[str, int]:
    """
    Saves file asynchronously in chunks.
    Returns (stored_name, size_bytes)
    """
    ensure_storage_dir()
    stored_name = f"{uuid.uuid4().hex}"
    path = build_path(stored_name)

    size = 0
    async with aiofiles.open(path, "wb") as out:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            await out.write(chunk)

    await file.close()
    return stored_name, size
