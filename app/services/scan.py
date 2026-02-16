import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.file import FileMeta

async def scan_file(file_id: int, db: AsyncSession):
    """
    Mock scan:
    - Wait 2 seconds
    - Mark CLEAN by default
    - Mark INFECTED if original name contains 'virus'
    """
    await asyncio.sleep(2)

    res = await db.execute(select(FileMeta).where(FileMeta.id == file_id))
    f = res.scalar_one_or_none()
    if not f:
        return

    name = (f.original_name or "").lower()
    f.scan_status = "INFECTED" if "virus" in name else "CLEAN"
    await db.commit()
