import os
from fastapi import (
    APIRouter, Depends, UploadFile, File, BackgroundTasks,
    HTTPException, Request, Query
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.signing import create_download_token, verify_download_token
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.file import FileMeta
from app.models.user import User
from app.services.storage import save_upload_file, build_path
from app.services.scan import scan_file
from app.utils.validators import validate_content_type, validate_file_size
from app.schemas.file import FileResponse

router = APIRouter(prefix="/files", tags=["Files"])

# Rate limiter (IP-based)
limiter = Limiter(key_func=get_remote_address)


def allowed_types_set() -> set[str]:
    return set(x.strip() for x in settings.ALLOWED_CONTENT_TYPES.split(",") if x.strip())


def max_bytes() -> int:
    return settings.MAX_FILE_SIZE_MB * 1024 * 1024


async def file_iterator(path: str, chunk_size: int = 1024 * 1024):
    import aiofiles
    async with aiofiles.open(path, "rb") as f:
        while chunk := await f.read(chunk_size):
            yield chunk

@router.post("/upload")
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Validate type
    validate_content_type(file.content_type or "", allowed_types_set())

    # Save file async (we get size after saving)
    stored_name, size = await save_upload_file(file)

    # Validate size (delete if too large)
    try:
        validate_file_size(size, max_bytes())
    except HTTPException:
        try:
            os.remove(build_path(stored_name))
        except OSError:
            pass
        raise

    # Store metadata
    meta = FileMeta(
        owner_id=user.id,
        original_name=file.filename or "unknown",
        stored_name=stored_name,
        size=size,
        content_type=file.content_type or "application/octet-stream",
        scan_status="PENDING",
    )
    db.add(meta)
    await db.commit()
    await db.refresh(meta)

    # Background scan (mock)
    background_tasks.add_task(scan_file, meta.id, db)

    return FileResponse(
        id=meta.id,
        owner_id=meta.owner_id,
        original_name=meta.original_name,
        size=meta.size,
        content_type=meta.content_type,
        scan_status=meta.scan_status,
        created_at=meta.created_at,
    )



@router.get("", response_model=list[FileResponse])
async def list_my_files(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == "admin":
        res = await db.execute(select(FileMeta).order_by(FileMeta.created_at.desc()))
    else:
        res = await db.execute(
            select(FileMeta)
            .where(FileMeta.owner_id == user.id)
            .order_by(FileMeta.created_at.desc())
        )

    files = res.scalars().all()
    return [
        FileResponse(
            id=f.id,
            owner_id=f.owner_id,
            original_name=f.original_name,
            size=f.size,
            content_type=f.content_type,
            scan_status=f.scan_status,
            created_at=f.created_at,
        )
        for f in files
    ]


@router.post("/{file_id}/signed-url")
async def create_signed_url(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(select(FileMeta).where(FileMeta.id == file_id))
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    # Only owner or admin can create signed URL
    if user.role != "admin" and f.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if f.scan_status == "PENDING":
        raise HTTPException(status_code=409, detail="File scan pending")
    if f.scan_status == "INFECTED":
        raise HTTPException(status_code=403, detail="File blocked (infected)")

    token = create_download_token(file_id=f.id, user_id=user.id, minutes=5)

    return {
        "expires_in_minutes": 5,
        "download_url": f"/files/token-download?token={token}"
    }


@router.get("/token-download")
@limiter.limit("30/minute")
async def download_with_token(
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    payload = verify_download_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid/expired token")

    file_id = payload.get("file_id")
    user_id = payload.get("user_id")
    if not file_id or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Get file
    res = await db.execute(select(FileMeta).where(FileMeta.id == int(file_id)))
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    # Get token user from DB
    res_user = await db.execute(select(User).where(User.id == int(user_id)))
    token_user = res_user.scalar_one_or_none()
    if not token_user:
        raise HTTPException(status_code=403, detail="Invalid user")

    # ✅ Allow if token_user is admin OR token_user is the owner
    if token_user.role != "admin" and f.owner_id != token_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if f.scan_status == "PENDING":
        raise HTTPException(status_code=409, detail="File scan pending")
    if f.scan_status == "INFECTED":
        raise HTTPException(status_code=403, detail="File blocked (infected)")

    path = build_path(f.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Stored file missing")

    headers = {"Content-Disposition": f'attachment; filename="{f.original_name}"'}
    return StreamingResponse(
        file_iterator(path),
        media_type=f.content_type,
        headers=headers,
    )

@router.get("/{file_id}", response_model=FileResponse)
async def get_file_meta(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(select(FileMeta).where(FileMeta.id == file_id))
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if user.role != "admin" and f.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return FileResponse(
        id=f.id,
        owner_id=f.owner_id,
        original_name=f.original_name,
        size=f.size,
        content_type=f.content_type,
        scan_status=f.scan_status,
        created_at=f.created_at,
    )


@router.get("/{file_id}/download")
@limiter.limit("30/minute")
async def download_file(
    request: Request,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(select(FileMeta).where(FileMeta.id == file_id))
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if user.role != "admin" and f.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if f.scan_status == "PENDING":
        raise HTTPException(status_code=409, detail="File scan pending")
    if f.scan_status == "INFECTED":
        raise HTTPException(status_code=403, detail="File blocked (infected)")

    path = build_path(f.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Stored file missing")

    headers = {"Content-Disposition": f'attachment; filename="{f.original_name}"'}
    return StreamingResponse(
        file_iterator(path),
        media_type=f.content_type,
        headers=headers,
    )
