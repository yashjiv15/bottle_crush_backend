from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import Token, UserLogin
from app.models import User
from app.core.security import create_access_token, verify_password, get_current_user
import jwt
from app.database import get_db

# Create APIRouter instance
router = APIRouter()



@router.post("/login/", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token with user role
    access_token = create_access_token(data={"sub": user.email, "role": db_user.role, "id": db_user.id})
    return {"access_token": access_token, "token_type": "bearer"}



# Role-based access control
def role_required(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Function to get a user by username
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()