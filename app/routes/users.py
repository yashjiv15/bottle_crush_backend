import logging
from fastapi import HTTPException, Depends, status, APIRouter, Request
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate
from app.core.security import hash_password
from app.database import get_db

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Validates if the email is already registered.
    - Hashes the password before saving it to the database.
    - Allows setting a role (default to 't_customer' if not specified).
    """
    try:
        # Check if the email already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email is already registered")
        
        # Hash the password before storing it
        hashed_password = hash_password(user.password)
        
        # Set default role if none is provided
        role = user.role if user.role else "t_customer"

        # Create a new user instance
        new_user = User(
            email=user.email,
            password=hashed_password,
            role=role
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "email": new_user.email,
            "role": new_user.role
        }
    
    except HTTPException as e:
        # Handle known exceptions like email duplication
        logger.error(f"Error registering user: {e.detail}")
        raise e
    
    except Exception as e:
        # Catch any unexpected errors
        logger.exception("Unexpected error occurred during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
