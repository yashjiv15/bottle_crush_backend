from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session, aliased
from app.models import Business
from app.schemas import  BusinessCreate, UserCreate, BusinessUpdate
from app.database import get_db
from app.models import User, Machine, Bottle
import os
from app.core.security import role_required, verify_token, get_current_user, pwd_context
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
from sqlalchemy import func, case
import bcrypt

router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

UPLOAD_DIRECTORY = "uploads/business_logos"  # Directory to save uploaded images

# Ensure the directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

router = APIRouter()

@router.post("/create_business", dependencies=[Depends(verify_token)], tags=["Admin-Business"])
async def create_business(
    business_data: str = Form(...),  # JSON string as input
    user_data: str = Form(...),      # JSON string as input
    logo_image: UploadFile = File(None),  # Optional file input
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("t_admin"))
):

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
            # Hash the password using the passlib context
            hashed_password = pwd_context.hash(user_data["password"])

            # Create a new user if none exists
            new_user = User(
                email=user_data["email"],
                password=hashed_password,  # Store the hashed password
                role='t_customer',
                created_by=current_user["id"],  # Use current_user.id for creation
                updated_by=current_user["id"],  # Use current_user.id for updates
            )
            db.add(new_user)
            db.commit()  # Auto-generate the 'id'
            db.refresh(new_user)  # Refresh to load the generated 'id'

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

    # Step 2: Validate if the Business already exists
    try:
        existing_business = db.query(Business).filter(Business.name == business_data["name"]).first()
        if existing_business:
            raise HTTPException(status_code=400, detail="Business with this name already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking business: {str(e)}")

    # Step 3: Handle the Logo File
    try:
        if logo_image:
            logo_binary = await logo_image.read()

            if len(logo_binary) > 5 * 1024 * 1024:  # 5MB limit
                raise HTTPException(status_code=400, detail="File is too large")
        else:
            logo_binary = None  # Set to None if no file is uploaded
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Step 4: Create the Business Record
    try:
        new_business = Business(
            name=business_data["name"],
            mobile=business_data["mobile"],
            logo_image=logo_binary,  # This can now be None if no file is uploaded
            business_owner=new_user.id,
            created_by=current_user["id"],  # Use current_user.id for creation
            updated_by=current_user["id"],  # Use current_user.id for updates
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

@router.get("/business/{business_id}", response_model=None, dependencies=[Depends(verify_token)], tags=["Admin-Business"])
async def get_business(business_id: int, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # If the logo_image is stored as bytes (e.g., in the database)
    if business.logo_image:
        logo_image_base64 = base64.b64encode(business.logo_image).decode('utf-8')
    else:
        logo_image_base64 = None  # If no image exists, return None or a default

    response_data = {
        "id": business.id,
        "name": business.name,
        "mobile": business.mobile,
        "logo_image": logo_image_base64,  # Send the Base64 string
        "created_by": business.created_by,
        "updated_by": business.updated_by,
        "created_at": business.created_at.isoformat(),  # Convert datetime to string
        "updated_at": business.updated_at.isoformat(),  # Convert datetime to string
    }

    return JSONResponse(content=response_data)


def serialize_business_with_owner(business, owner_email):
    """Convert SQLAlchemy business object to a JSON-serializable dictionary and include owner email."""
    business_dict = {key: value for key, value in vars(business).items() if not key.startswith("_")}

    # Handle datetime objects
    for key, value in business_dict.items():
        if isinstance(value, datetime):
            business_dict[key] = value.isoformat()

    # Handle binary logo image
    if business_dict.get("logo_image") is not None:
        business_dict["logo_image"] = base64.b64encode(business_dict["logo_image"]).decode("utf-8")

    # Add the owner's email
    business_dict["owner_email"] = owner_email

    return business_dict

@router.get("/businesses", response_model=None, dependencies=[Depends(verify_token)], tags=["Admin-Business"])
async def get_all_businesses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Fetch businesses with owner email
    businesses = (
        db.query(Business, User.email.label("owner_email"))
        .join(User, Business.business_owner == User.id)  # Join Business with User table
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not businesses:
        raise HTTPException(status_code=404, detail="No businesses found")

    # Serialize businesses
    serialized_businesses = [
        serialize_business_with_owner(business, owner_email) for business, owner_email in businesses
    ]

    return JSONResponse(content={"businesses": serialized_businesses})


@router.delete("/business/{business_id}", dependencies=[Depends(verify_token)], tags=["Admin-Business"])
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

@router.get("/my-business", response_model=None, dependencies=[Depends(verify_token)], tags=["Customer-Business"])
async def get_my_businesses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Fetch businesses for the current authenticated user
    businesses = (
        db.query(Business, User.email.label("owner_email"))
        .join(User, Business.business_owner == User.id)  # Join Business with User table
        .filter(Business.business_owner == current_user["id"])  # Filter by current user's ID
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not businesses:
        raise HTTPException(status_code=404, detail="No businesses found for the current user")

    # Serialize businesses
    serialized_businesses = [
        serialize_business_with_owner(business, owner_email) for business, owner_email in businesses
    ]

    return JSONResponse(content={"businesses": serialized_businesses})

@router.put("/businesses/{business_id}", dependencies=[Depends(verify_token)], tags=["Admin-Business"])
async def update_business(
    business_id: int,
    business_data: BusinessUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing business by its ID.
    """
    # Fetch the business by ID
    db_business = db.query(Business).filter(Business.id == business_id).first()
    if db_business is None:
        raise HTTPException(status_code=404, detail="Business not found")

    # Update business details
    db_business.name = business_data.name
    db_business.mobile = business_data.mobile
    db_business.updated_at = datetime.utcnow()

    # Commit the changes
    db.commit()
    db.refresh(db_business)

    # Return the updated business
    return {
        "message": "Business updated successfully",
        "business": {
            "id": db_business.id,
            "name": db_business.name,
            "mobile": db_business.mobile,
            "created_by": db_business.created_by,
            "updated_by": db_business.updated_by,
            "created_at": db_business.created_at,
            "updated_at": db_business.updated_at,
        },
    }


@router.get("/business-count", response_model=int, dependencies=[Depends(verify_token)], tags=["Admin-Dashboard"])
async def get_business_count(db: Session = Depends(get_db)):
    """
    Fetch the total count of businesses.
    """
    # Query to count the total number of businesses
    business_count = db.query(func.count(Business.id)).scalar()

    return business_count


@router.get("/business-stats/{business_id}", dependencies=[Depends(verify_token)], tags=["Admin-Dashboard"])
async def get_business_stats(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required("t_admin"))
):
    """
    Get total machine count, total bottle count, and total bottle weight for a given business ID.
    """
    # Validate the business
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Subquery for bottle statistics grouped by machine
    bottle_stats_subquery = (
        db.query(
            Bottle.machine_id.label("machine_id"),
            func.sum(Bottle.bottle_count).label("total_bottle_count"),
            func.sum(Bottle.bottle_weight).label("total_bottle_weight"),
        )
        .group_by(Bottle.machine_id)
        .subquery()
    )

    # Main query to calculate machine count
    machine_count_query = db.query(func.count(Machine.id).label("total_machines")).filter(Machine.business_id == business_id)

    # Fetch machine count
    total_machines = machine_count_query.scalar()

    # Fetch aggregated bottle stats directly
    bottle_stats_query = (
        db.query(
            func.coalesce(func.sum(bottle_stats_subquery.c.total_bottle_count), 0).label("total_bottle_count"),
            func.coalesce(func.sum(bottle_stats_subquery.c.total_bottle_weight), 0.0).label("total_bottle_weight"),
        )
        .join(Machine, Machine.id == bottle_stats_subquery.c.machine_id)
        .filter(Machine.business_id == business_id)
    )

    bottle_stats = bottle_stats_query.first()
    total_bottle_count = bottle_stats.total_bottle_count
    total_bottle_weight = bottle_stats.total_bottle_weight

    # Return the results
    return {
        "business_id": business_id,
        "business_name": business.name,
        "total_machines": total_machines,
        "total_bottle_count": total_bottle_count,
        "total_bottle_weight": total_bottle_weight,
    }

@router.put("/update_business/{business_id}", dependencies=[Depends(verify_token)], tags=["Admin-Business"])
async def update_business(
    business_id: int,
    business_data: str = Form(...),  # JSON string as input
    user_data: str = Form(...),      # JSON string as input
    logo_image: UploadFile = File(None),  # Optional file input
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("t_admin"))
):

    try:
        # Parse the JSON data
        business_data = json.loads(business_data)
        user_data = json.loads(user_data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {e}")

    # Step 1: Get the Business Record
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Step 2: Validate the User Record and Update
    user = db.query(User).filter(User.id == business.business_owner).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user email if changed
    if "email" in user_data and user_data["email"] != user.email:
        # Check if the new email already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_data["email"]
    
    # Update password if provided, using the same hashing logic
    if "password" in user_data:
        # Hash the new password using the passlib context
        user.password = pwd_context.hash(user_data["password"])
    
    # Commit the user updates
    user.updated_by = current_user["id"]
    db.commit()
    db.refresh(user)

    # Step 3: Handle Logo File if Provided
    if logo_image:
        logo_binary = await logo_image.read()
        if len(logo_binary) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File is too large")
        business.logo_image = logo_binary  # Update logo file if a new one is uploaded

    # Step 4: Update Business Record
    if "name" in business_data:
        business.name = business_data["name"]
    if "mobile" in business_data:
        business.mobile = business_data["mobile"]

    business.updated_by = current_user["id"]  # Update the "updated_by" field
    db.commit()
    db.refresh(business)

    return JSONResponse(content={
        "message": "Business and user updated successfully",
        "business_id": business.id,
        "user_id": user.id,
    })
