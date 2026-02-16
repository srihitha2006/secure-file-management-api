from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.db.session import engine
from app.db.base import Base

from app.models.user import User  # noqa: F401
from app.models.file import FileMeta  # noqa: F401

from app.api.routes.auth import router as auth_router
from app.api.routes.files import router as files_router, limiter

app = FastAPI(title="Secure File Management API")

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth_router)
app.include_router(files_router)

@app.get("/")
def root():
    return {"message": "API running"}
