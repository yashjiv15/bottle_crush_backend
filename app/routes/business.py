from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.models import Business
from app.schemas import BusinessCreate
from app.database import get_db
from app.models import User
import os
from app.core.security import role_required
from uuid import uuid4 
from datetime import datetime
from sqlalchemy.exc import IntegrityError

router = APIRouter()

UPLOAD_DIRECTORY = "uploads/business_logos"  # Directory to save uploaded images

# Ensure the directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


router = APIRouter()

@router.post("/create_business")
def create_business(
    name: str,
    email: str,
    mobile: str,
    created_by: int,
    created_at: str,
    updated_by: int,
    updated_at: str,
    files: UploadFile = File(...),  # Single file upload (logo image)
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("t_admin"))
):
    """
    Create a business. Accessible only to users with t_admin role.
    """

    # Convert string to datetime objects
    created_at = datetime.fromisoformat(created_at)
    updated_at = datetime.fromisoformat(updated_at)

    # Ensure the upload directory exists
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    # Check if the file is received correctly
    if files:
        print(f"Received file: {files.filename}")  # This is for debugging

        # Get the file name from the uploaded file
        file_name = files.filename

        # Ensure the file name is unique (optional step to avoid overwriting)
        file_name = f"{str(uuid4())}_{file_name}"

        # Construct the full path to save the logo image
        file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

        # Save the logo image to the file system
        with open(file_path, "wb") as f:
            f.write(files.file.read())
    else:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Check if mobile number already exists
    existing_business = db.query(Business).filter(Business.mobile == mobile).first()
    if existing_business:
        raise HTTPException(status_code=400, detail="Business with this mobile number already exists")

    try:
        # Create business
        new_business = Business(
            name=name,
            email=email,
            mobile=mobile,
            logo_image=file_path,  # Store the file path to the logo image
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at,
        )

        db.add(new_business)
        db.commit()
        db.refresh(new_business)

        return {"message": "Business created successfully", "business_id": new_business.id}

    except IntegrityError as e:
        db.rollback()  # Rollback the transaction in case of an error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error: A business with this mobile number already exists."
        )
    except Exception as e:
        db.rollback()  # Rollback for any unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the business."
        )