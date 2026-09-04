from typing import Literal
from pydantic import BaseModel, EmailStr
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
