from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import hash_password, verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):

    # Debug (keep for now)
    print("REGISTER HIT ✅")
    print("PASSWORD LEN =", len(data.password.encode("utf-8")))
    print("PASSWORD REPR =", repr(data.password))

    # bcrypt limit
    if len(data.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 bytes for bcrypt)")

    # check existing email
    res = await db.execute(select(User).where(User.email == data.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    role = data.role.lower()
    if role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")

    # ✅ IMPORTANT: hash_password ONLY (do NOT call verify here)
    hashed = hash_password(data.password)

    user = User(email=data.email, hashed_password=hashed, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(id=user.id, email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == data.email))
    user = res.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email, role=user.role)
