import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.crud import get_user_by_username, verify_password, hash_password
from app.schemas import UserLogin, Token, UserCreate
import jwt
from datetime import datetime, timedelta
from app.models import SessionLocal, User


# Create the FastAPI app instance
app = FastAPI()


# Secret key for JWT encoding/decoding
SECRET_KEY = "bottle_crush_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to create a superadmin user if it doesn't exist
def create_superadmin(db: Session):
    superadmin = db.query(User).filter(User.email == "superadmin").first()
    if not superadmin:
        hashed_password = hash_password("superadminpassword")  # Set a default password
        superadmin = User(email="superadmin", password=hashed_password, role="t_admin", is_active=True)
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        print("Superadmin user created!")
    else:
        print("Superadmin already exists.")


@app.on_event("startup")
def on_startup():
    # Create superadmin user at startup if it doesn't exist
    db = SessionLocal()
    create_superadmin(db)
    db.close()

@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password before saving
    hashed_password = hash_password(user.password)
    
    # Create new user with the specified role
    new_user = User(username=user.username, password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully"}

@app.post("/login/", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token with user role
    access_token = create_access_token(data={"sub": user.username, "role": db_user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# Function to get the current user from the JWT token
def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")
    
    try:
        token = token.split(" ")[1]  # Extract Bearer token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Contains {"sub": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

# Role-based access control
def role_required(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

@app.get("/admin/")
def admin_area(current_user: dict = Depends(role_required("t_admin"))):
    return {"message": "Welcome to the admin area", "user": current_user}


@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI app with SQLite!"}

# Enable running with Uvicorn for local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",  # Use the app instance defined above
        host=os.getenv("HOST", "127.0.0.1"),  # Default to localhost
        port=int(os.getenv("PORT", 8000)),    # Default to port 8000
        reload=True                           # Enable auto-reload for development
    )
