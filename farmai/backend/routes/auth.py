"""User authentication routes: Register (Sign up), Login (Sign in), Logout, and Current User profile.
"""
import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.database import get_db
from database.orm_models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = "krishinetra-production-secret-offline-key"


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "krishinetra_salt"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


class SignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str
    preferred_language: Optional[str] = "en"


class SignInRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    preferred_language: str
    token: str


@router.post("/signup", response_model=UserResponse)
def sign_up(payload: SignUpRequest, db: Session = Depends(get_db)):
    """Register a new farmer account."""
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in."
        )

    if len(payload.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters long."
        )

    new_user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
        preferred_language=payload.preferred_language or "en"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = f"knetra_{new_user.id}_{secrets.token_hex(16)}"
    return UserResponse(
        id=new_user.id,
        full_name=new_user.full_name,
        email=new_user.email,
        preferred_language=new_user.preferred_language,
        token=token
    )


@router.post("/signin", response_model=UserResponse)
def sign_in(payload: SignInRequest, db: Session = Depends(get_db)):
    """Authenticate and sign in an existing farmer account."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    token = f"knetra_{user.id}_{secrets.token_hex(16)}"
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        preferred_language=user.preferred_language,
        token=token
    )


@router.post("/logout")
def logout():
    """Sign out the current session."""
    return {"status": "success", "message": "Logged out successfully."}


@router.get("/me")
def get_me(token: Optional[str] = None, db: Session = Depends(get_db)):
    """Verify session token and retrieve active user profile."""
    if not token or not token.startswith("knetra_"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        parts = token.split("_")
        user_id = int(parts[1])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        return {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "preferred_language": user.preferred_language
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.")
