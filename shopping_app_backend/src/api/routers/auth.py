from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.db.session import get_db
from src.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.api.services import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register a new user",
    description="Creates a user account and returns a JWT access token.",
    operation_id="auth_register",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user, token = register_user(db, email=payload.email, password=payload.password, full_name=payload.full_name)
    return TokenResponse(access_token=token, token_type="bearer")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticates a user and returns a JWT access token.",
    operation_id="auth_login",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user, token = login_user(db, email=payload.email, password=payload.password)
    return TokenResponse(access_token=token, token_type="bearer")
