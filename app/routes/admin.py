
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import hash_password, verify_token
from app.schemas import BusinessCreate
from app.models import User
from app.core.security import role_required

# Create APIRouter instance
router = APIRouter()

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

    
@router.get("/admin/", dependencies=[Depends(verify_token)], tags=["Admin"])
def admin_area(current_user: dict = Depends(role_required("t_admin"))):
    return {"message": "Welcome to the admin area", "user": current_user}


