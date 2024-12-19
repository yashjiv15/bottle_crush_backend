# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str
    role: str  # Role is required in registration
    is_active: bool = True
    is_deleted: bool = False

    class Config:
        orm_mode = True


class BusinessCreate(BaseModel):
    name: str
    email: str
    mobile: str
    logo_image: str  # Path to the logo image (assuming it's already uploaded somewhere)
    created_by: int
    updated_by: int
    created_at: datetime = datetime.utcnow()  # Default to current timestamp
    updated_at: datetime = datetime.utcnow()  # Default to current timestamp

    class Config:
        orm_mode = True