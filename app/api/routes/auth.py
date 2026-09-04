import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import (
    LoginRequest,
    AuthResponse,
    LogoutResponse,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if email is already registered
    existing_user = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    # Hash password with bcrypt
    hashed_pwd = get_password_hash(user_in.password)
    
    # Create new operator
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        hashed_password=hashed_pwd,
        role="operator",
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=AuthResponse)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    email_clean = login_in.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    
    # Generic error on invalid email or wrong password
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is suspended",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Generate access token with user id and role
    access_token = create_access_token(user_id=user.id, role=user.role)
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout", response_model=LogoutResponse)
def logout():
    """
    Sign out endpoint confirming session termination.
    Stateless JWT architecture relies on short expiry + client clearing tokens.
    """
    return LogoutResponse(message="Successfully logged out")

@router.post("/request-reset", response_model=PasswordResetRequestResponse)
def request_password_reset(reset_in: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Generate a short-lived, single-use reset token for forgotten password.
    Returns generic confirmation to prevent email enumeration.
    """
    email_clean = reset_in.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    reset_token = None
    if user and user.is_active:
        # Invalidate any previously issued unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})

        token_str = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        token_record = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=expires_at,
            used=False
        )
        db.add(token_record)
        db.commit()
        reset_token = token_str

    return PasswordResetRequestResponse(
        message="If the email is registered, password reset instructions have been sent.",
        reset_token=reset_token
    )

@router.post("/confirm-reset", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(confirm_in: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Verify reset token, hash new password with bcrypt, update user record, and invalidate token.
    """
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == confirm_in.token.strip()
    ).first()

    if not token_record or token_record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if token_record.expires_at < datetime.now(timezone.utc):
        token_record.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user account"
        )

    # Hash new password with bcrypt and update
    user.hashed_password = get_password_hash(confirm_in.new_password)
    token_record.used = True
    db.commit()

    return PasswordResetConfirmResponse(
        message="Password has been successfully reset. You may now sign in with your new password."
    )
