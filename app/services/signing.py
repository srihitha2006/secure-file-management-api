from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt, JWTError

from app.core.config import settings

# separate purpose so it can't be used as login token
DOWNLOAD_TOKEN_AUD = "file-download"


def create_download_token(file_id: int, user_id: int, minutes: int = 5) -> str:
    payload: Dict[str, Any] = {
        "aud": DOWNLOAD_TOKEN_AUD,
        "file_id": file_id,
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def verify_download_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            audience=DOWNLOAD_TOKEN_AUD
        )
        return payload
    except JWTError:
        return {}
