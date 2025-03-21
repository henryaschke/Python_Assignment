from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User's full name")

class UserCreate(UserBase):
    password: str = Field(..., description="User password (will be hashed)")

class User(UserBase):
    User_ID: int = Field(..., description="User ID")
    is_active: bool = Field(True, description="Whether the user is active")
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password") 