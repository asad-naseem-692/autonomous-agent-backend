from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, AuthResponse, LogoutResponse
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
