# crud.py
from sqlalchemy.orm import Session
from app.models import User
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash passwords
def hash_password(password: str):
    return pwd_context.hash(password)

# Function to verify passwords
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Function to create a new user
def create_user(db: Session, username: str, password: str):
    hashed_password = hash_password(password)
    db_user = User(username=username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Function to get a user by username
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
