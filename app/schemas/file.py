from datetime import datetime
from pydantic import BaseModel

class FileResponse(BaseModel):
    id: int
    owner_id: int
    original_name: str
    size: int
    content_type: str
    scan_status: str
    created_at: datetime
