import time
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from config.settings import settings
from storage.db import get_db
from storage.repositories.user_repository import UserRepository
from backend.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token
)
from backend.core.logging_setup import log_security_event
from backend.api.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, RefreshTokenRequest, UserResponse
)
from backend.api.deps import get_current_user, CurrentUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_211_CREATED if hasattr(status, "HTTP_211_CREATED") else 201)
def register(
    req: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    repo = UserRepository(db)

    # Check if username or email already exists
    if repo.get_by_username(req.username):
        log_security_event(
            event_type="AUTH_REGISTER_FAIL",
            message=f"Registration failed: username '{req.username}' already exists",
            src_ip=client_ip,
            level=30
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USERNAME_EXISTS", "message": f"Username '{req.username}' is already registered."}
        )

    if repo.get_by_email(req.email):
        log_security_event(
            event_type="AUTH_REGISTER_FAIL",
            message=f"Registration failed: email '{req.email}' already exists",
            src_ip=client_ip,
            level=30
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMAIL_EXISTS", "message": f"Email '{req.email}' is already registered."}
        )

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    hashed_pwd = hash_password(req.password)
    user = repo.create_user(
        user_id=user_id,
        username=req.username,
        email=req.email,
        hashed_password=hashed_pwd,
        role=req.role or "analyst",
        created_ts=time.time()
    )

    log_security_event(
        event_type="AUTH_REGISTER_SUCCESS",
        message=f"User '{user.username}' registered successfully with role '{user.role}'",
        src_ip=client_ip,
        user_id=user.user_id
    )

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_ts=user.created_ts
    )


@router.post("/login", response_model=TokenResponse)
def login(
    req: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    repo = UserRepository(db)

    user = repo.get_by_username(req.username_or_email)
    if not user:
        user = repo.get_by_email(req.username_or_email)

    if not user or not verify_password(req.password, user.hashed_password):
        log_security_event(
            event_type="AUTH_LOGIN_FAILED",
            message=f"Failed login attempt for identifier '{req.username_or_email}'",
            src_ip=client_ip,
            level=30
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username/email or password."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_security_event(
            event_type="AUTH_LOGIN_DISABLED",
            message=f"Login attempt for disabled account '{user.username}'",
            src_ip=client_ip,
            user_id=user.user_id,
            level=30
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "User account is disabled."}
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role, "uid": user.user_id})
    refresh_token = create_refresh_token(data={"sub": user.username, "uid": user.user_id})

    log_security_event(
        event_type="AUTH_LOGIN_SUCCESS",
        message=f"User '{user.username}' logged in successfully",
        src_ip=client_ip,
        user_id=user.user_id
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    req: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token.")
        
        username = payload.get("sub")
        repo = UserRepository(db)
        user = repo.get_by_username(username)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive.")

        access_token = create_access_token(data={"sub": user.username, "role": user.role, "uid": user.user_id})
        new_refresh_token = create_refresh_token(data={"sub": user.username, "uid": user.user_id})

        log_security_event(
            event_type="AUTH_TOKEN_REFRESH",
            message=f"Refreshed token for user '{user.username}'",
            src_ip=client_ip,
            user_id=user.user_id
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except Exception as exc:
        log_security_event(
            event_type="AUTH_REFRESH_FAILED",
            message=f"Token refresh failed: {str(exc)}",
            src_ip=client_ip,
            level=30
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
def logout(current_user: CurrentUser = Depends(get_current_user)):
    log_security_event(
        event_type="AUTH_LOGOUT",
        message=f"User '{current_user.username}' logged out",
        user_id=current_user.user_id
    )
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_ts=time.time()
    )
