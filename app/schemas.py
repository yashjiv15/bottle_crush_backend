# schemas.py
from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
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