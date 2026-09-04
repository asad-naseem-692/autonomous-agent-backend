from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse

class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetRequestResponse(BaseModel):
    message: str = "If the email is registered, password reset instructions have been sent."
    reset_token: Optional[str] = None

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class PasswordResetConfirmResponse(BaseModel):
    message: str = "Password has been successfully reset. You may now sign in with your new password."
