from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.models import Business
from app.schemas import  BusinessCreate, UserCreate
from app.database import get_db
from app.models import User
import os
from app.core.security import role_required, verify_token
from uuid import uuid4 
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.routes.users import register_user as create_user
import json
import hashlib  # Assuming you are hashing passwords
import logging
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import base64
from fastapi.encoders import jsonable_encoder

router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

UPLOAD_DIRECTORY = "uploads/business_logos"  # Directory to save uploaded images

# Ensure the directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

router = APIRouter()

@router.post("/create_business", dependencies=[Depends(verify_token)])
async def create_business(
    business_data: str = Form(...),  # JSON string as input
    user_data: str = Form(...),      # JSON string as input
    logo_image: UploadFile = File(...),  # File input
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("t_admin"))
):
    
    print("Received current_user:", current_user)
    
    try:
        # Parse the JSON data
        business_data = json.loads(business_data)
        user_data = json.loads(user_data)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {e}")

    # Step 1: Validate and Create the User
    try:
        # Check if the email is already registered
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            print("User with this email already exists. Proceeding with business creation.")
            new_user = existing_user  # Use the existing user if found
        else:
            # If the user does not exist, create a new user
            new_user = User(
                email=user_data["email"],
                password=user_data["password"],  # Ensure password is hashed
                role=user_data["role"],
                is_active=user_data["is_active"],
                is_deleted=user_data["is_deleted"],
                created_by=current_user["id"],  # Change from current_user.id to current_user["id"]
                updated_by=current_user["id"],  # Change from current_user.id to current_user["id"]
            )
            
            db.add(new_user)
            db.commit()  # This will auto-generate the 'id'
            db.refresh(new_user)  # Refresh the object to load the generated 'id'
            user_id = new_user.id  # Access the auto-generated 'id'

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

    # Step 2: Validate if the Business already exists
    try:
        # Check if a business with the same name or unique field already exists
        existing_business = db.query(Business).filter(Business.name == business_data["name"]).first()
        if existing_business:
            raise HTTPException(status_code=400, detail="Business with this name already exists")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking business: {str(e)}")

    # Step 3: Handle the Logo File
    try:
        logo_binary = await logo_image.read()

        if len(logo_binary) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File is too large")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Step 4: Create the Business Record
    try:
        new_business = Business(
            name=business_data["name"],
            mobile=business_data["mobile"],
            logo_image=logo_binary,
            business_owner=new_user.id,  # This should now work
            created_by=current_user["id"],  # Change from current_user.id to current_user["id"]
            updated_by=current_user["id"],  # Change from current_user.id to current_user["id"]
            created_at=business_data["created_at"],
            updated_at=business_data["updated_at"],
        )
        db.add(new_business)
        db.commit()
        db.refresh(new_business)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating business: {str(e)}")

    return JSONResponse(content={
        "message": "Business and user created successfully",
        "business_id": new_business.id,
        "user_id": new_user.id,
    })



@router.get("/business/{business_id}", response_model=None, dependencies=[Depends(verify_token)])
async def get_business(business_id: int, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    response_data = {
        "id": business.id,
        "name": business.name,
        "mobile": business.mobile,
        "created_by": business.created_by,
        "updated_by": business.updated_by,
        "created_at": business.created_at.isoformat(),  # Convert datetime to string
        "updated_at": business.updated_at.isoformat(),  # Convert datetime to string
    }

    return JSONResponse(content=response_data)


def serialize_business(business):
    """Convert SQLAlchemy object to a JSON-serializable dictionary."""
    business_dict = {key: value for key, value in vars(business).items() if not key.startswith("_")}
    if business_dict.get("logo_image"):
        business_dict["logo_image"] = base64.b64encode(business_dict["logo_image"]).decode("utf-8")
    return business_dict

def serialize_business(business):
    """Convert SQLAlchemy object to a JSON-serializable dictionary."""
    business_dict = {key: value for key, value in vars(business).items() if not key.startswith("_")}
    
    # Handle datetime objects
    for key, value in business_dict.items():
        if isinstance(value, datetime):
            business_dict[key] = value.isoformat()

    # Handle binary logo image
    if business_dict.get("logo_image"):
        business_dict["logo_image"] = base64.b64encode(business_dict["logo_image"]).decode("utf-8")

    return business_dict

@router.get("/businesses", response_model=None, dependencies=[Depends(verify_token)])
async def get_all_businesses(skip: int = 0,
    limit: int = 100, db: Session = Depends(get_db)):
    # Fetch all businesses
    businesses = db.query(Business).all()

    if not businesses:
        raise HTTPException(status_code=404, detail="No businesses found")

    # Serialize each business
    serialized_businesses = [serialize_business(business) for business in businesses]

    return JSONResponse(content={"businesses": serialized_businesses})


@router.delete("/business/{business_id}", dependencies=[Depends(verify_token)])
async def delete_business(
    business_id: int, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(role_required("t_admin"))
):
    """
    Delete a business by its ID.
    Only allowed for users with the "t_admin" role.
    """
    # Fetch the business record
    business = db.query(Business).filter(Business.id == business_id).first()

    # If the business does not exist, raise a 404 error
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Optional: Check if the user is authorized to delete the business
    if current_user["role"] != "t_admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this business")

    try:
        # Delete the business
        db.delete(business)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting business: {str(e)}")

    return {"message": "Business deleted successfully", "business_id": business_id}