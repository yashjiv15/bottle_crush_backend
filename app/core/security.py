from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Secret key for JWT encoding/decoding
SECRET_KEY = "bottle_crush_secret_key"
ALGORITHM = "HS256"

# Define the HTTPBearer instance
security = HTTPBearer()


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Function to create JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to hash passwords
def hash_password(password: str):
    return pwd_context.hash(password)

# Function to verify passwords
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Role-based access control
def role_required(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker


# Function to get the current user from the JWT token
def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if token is None:
        print("No token provided")
        raise HTTPException(status_code=403, detail="Not authenticated")
    
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Invalid token format")
    
    try:
        token = token.split(" ")[1]  # Extract Bearer token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Contains {"sub": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

# Dependency to verify the token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials  # Extract the token from the header

    try:
        # Decode the token to validate it
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
        )

    # Optionally, you can extract user info from the payload
    # For example, assuming the JWT contains 'sub' (subject), which is the user identifier:
    user_id = payload.get("sub")

    return payload  # Optionally return the decoded payload (contains user info, etc.)
