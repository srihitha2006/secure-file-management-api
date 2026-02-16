from fastapi import HTTPException, status

def validate_content_type(content_type: str, allowed: set[str]):
    if content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}",
        )

def validate_file_size(size_bytes: int, max_bytes: int):
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max allowed is {max_bytes} bytes",
        )
