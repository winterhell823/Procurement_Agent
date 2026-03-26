from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

from models.base import get_db
from models.user import User
from config import settings

router = APIRouter()

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email:           EmailStr
    password:        str
    full_name:       str
    company_name:    Optional[str] = None
    contact_person:  Optional[str] = None
    company_phone:   Optional[str] = None
    company_address: Optional[str] = None
    payment_terms:   Optional[str] = None
    gst_number:      Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class UserOut(BaseModel):
    id:              uuid.UUID
    email:           str
    full_name:       str
    company_name:    Optional[str]
    contact_person:  Optional[str]
    company_phone:   Optional[str]
    company_address: Optional[str]
    payment_terms:   Optional[str]
    gst_number:      Optional[str]
    is_admin:        bool

    class Config:
        from_attributes = True


# ── JWT helpers ───────────────────────────────────────────────────────────────
def _create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# ── Auth dependency (used by every protected route) ───────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exc
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=pwd_ctx.hash(body.password),
        full_name=body.full_name,
        company_name=body.company_name,
        contact_person=body.contact_person,
        company_phone=body.company_phone,
        company_address=body.company_address,
        payment_terms=body.payment_terms,
        gst_number=body.gst_number,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form.username))
    user: User | None = result.scalar_one_or_none()

    if not user or not pwd_ctx.verify(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    return {"access_token": _create_token(str(user.id))}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_profile(
    body:         RegisterRequest,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    for field in [
        "full_name", "company_name", "contact_person",
        "company_phone", "company_address", "payment_terms", "gst_number",
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(current_user, field, val)

    if body.password:
        current_user.hashed_password = pwd_ctx.hash(body.password)

    await db.commit()
    await db.refresh(current_user)
    return current_user