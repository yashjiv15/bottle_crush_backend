import logging
from fastapi import HTTPException, Depends, status, APIRouter, Request
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate, ForgotPasswordRequest, VerifyOtpRequest, ResetPasswordRequest
from app.core.security import hash_password, create_access_token, SECRET_KEY, ALGORITHM
from app.database import get_db
from app.core.security import verify_token
from fastapi_mail import MessageSchema
from sqlalchemy.orm import Session
from app.core.email_settings import fast_mail
from datetime import datetime, timedelta
import random
import jwt
from fastapi.responses import JSONResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register/", tags=["Admin-Customer"])
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

# Get all users
@router.get("/users/", dependencies=[Depends(verify_token)], tags=["Admin-Customer"])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/users/forgot-password", tags=["Admin-Customer"] )
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Verify if the user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # Generate an OTP
    otp = str(random.randint(100000, 999999))  # 6-digit OTP
    otp_expiration = datetime.utcnow() + timedelta(minutes=15)  # OTP valid for 15 minutes

    # Save the OTP and expiration in the database
    user.reset_otp = otp
    user.reset_otp_expiration = otp_expiration
    db.commit()

    # Construct the email message
    email_body = f"""
    Hi {user.email},

    You requested a password reset. Use the following OTP to reset your password:
    {otp}

    This OTP is valid for 15 minutes. If you didn't request this, please ignore this email.
    """

    message = MessageSchema(
        subject="Password Reset OTP",
        recipients=[user.email],  # List of recipients
        body=email_body,
        subtype="html",
    )

    # Send the email
    await fast_mail.send_message(message)

    return {"message": "Password reset OTP has been sent to your email"}


@router.post("/users/verify-otp", tags=["Admin-Customer"])
async def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate OTP and expiration
    if user.reset_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if datetime.utcnow() > user.reset_otp_expiration:
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Create a short-lived JWT token for password reset
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(minutes=15)  # Token valid for 15 minutes
    }
    reset_token = create_access_token(token_data)

    return {"message": "OTP verified successfully", "reset_token": reset_token}

@router.post("/users/reset-password", tags=["Admin-Customer"])
async def reset_password(
    request: ResetPasswordRequest,  # Accept the request body as JSON
    db: Session = Depends(get_db),
):
    # Decode and verify the reset token
    try:
        payload = jwt.decode(request.reset_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    # Extract user details from the token
    email = payload.get("sub")
    user_id = payload.get("user_id")
    if not email or not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    # Fetch the user from the database
    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash the new password and update the user's record
    hashed_password = hash_password(request.new_password)
    user.password = hashed_password
    db.commit()

    return {"message": "Password reset successfully"}

@router.post("/logout", tags=["Admin-Customer"])
async def logout():
    """
    Logout the user by clearing session cookies.
    """
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie("session_id")
    return response
