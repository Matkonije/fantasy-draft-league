from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import Token, UserOut, UserRegister
from app.services.auth import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Session = Depends(get_db)):
    exists = db.scalar(
        select(User).where((User.email == body.email.lower()) | (User.username == body.username))
    )
    if exists:
        raise HTTPException(status_code=409, detail="Email or username already taken")

    # first registered user becomes admin
    user_count = db.scalar(select(func.count()).select_from(User))
    user = User(
        email=body.email.lower(),
        username=body.username,
        hashed_password=hash_password(body.password),
        is_admin=user_count == 0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form.username accepts either email or username
    user = db.scalar(
        select(User).where((User.email == form.username.lower()) | (User.username == form.username))
    )
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email/username or password")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
