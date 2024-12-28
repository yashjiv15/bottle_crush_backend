from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Machine, Bottle, User, Business
from app.schemas import BottleCreate
from app.database import get_db
from datetime import datetime
from app.core.security import role_required, verify_token
from sqlalchemy.orm import aliased
from sqlalchemy import func
from typing import Dict

router = APIRouter()

@router.post("/create_bottle/", tags=["Bottles"])
async def create_bottle(
    bottle: BottleCreate,  # Assuming you have a Pydantic model BottleCreate
    db: Session = Depends(get_db)
):
    # Check if the machine exists
    machine = db.query(Machine).filter(Machine.id == bottle.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Create a new bottle entry
    db_bottle = Bottle(
        machine_id=bottle.machine_id,
        bottle_count=bottle.bottle_count,
        bottle_weight=bottle.bottle_weight,
        created_by=1,  # User creating the entry
        updated_by=1,  # User updating the entry
    )
    db.add(db_bottle)
    db.commit()
    db.refresh(db_bottle)
    return db_bottle


@router.get("/bottles/",  dependencies=[Depends(verify_token)], tags=["Bottles"])
async def get_all_bottles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # Query all bottle entries with machine and user details
    bottles = (
        db.query(
            Bottle.id,
            Bottle.bottle_count,
            Bottle.bottle_weight,
            Machine.name.label("machine_name"),
            User.email.label("creator_name"),
            User.email.label("updater_name"),
            Bottle.created_at,
            Bottle.updated_at,
        )
        .join(Machine, Bottle.machine_id == Machine.id)
        .join(User, Bottle.created_by == User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": bottle.id,
            "bottle_count": bottle.bottle_count,
            "bottle_weight": bottle.bottle_weight,
            "machine_name": bottle.machine_name,
            "creator_name": bottle.creator_name,
            "updater_name": bottle.updater_name,
            "created_at": bottle.created_at,
            "updated_at": bottle.updated_at,
        }
        for bottle in bottles
    ]


@router.get("/bottle/{bottle_id}",  dependencies=[Depends(verify_token)], tags=["Bottles"])
async def get_bottle(
    bottle_id: int,
    db: Session = Depends(get_db),
):
    creator = aliased(User)
    updater = aliased(User)

    # Query bottle entry with related machine and user details
    bottle = (
        db.query(
            Bottle.id,
            Bottle.bottle_count,
            Bottle.bottle_weight,
            Machine.name.label("machine_name"),
            creator.email.label("creator_name"),
            updater.email.label("updater_name"),
            Bottle.created_at,
            Bottle.updated_at,
        )
        .join(Machine, Bottle.machine_id == Machine.id)
        .join(creator, Bottle.created_by == creator.id)
        .join(updater, Bottle.updated_by == updater.id)
        .filter(Bottle.id == bottle_id)
        .first()
    )

    if bottle is None:
        raise HTTPException(status_code=404, detail="Bottle not found")

    return {
        "id": bottle.id,
        "bottle_count": bottle.bottle_count,
        "bottle_weight": bottle.bottle_weight,
        "machine_name": bottle.machine_name,
        "creator_name": bottle.creator_name,
        "updater_name": bottle.updater_name,
        "created_at": bottle.created_at,
        "updated_at": bottle.updated_at,
    }

@router.get("/bottle-stats", response_model=Dict[str, float],  dependencies=[Depends(verify_token)], tags=["Bottles"])
async def get_bottle_stats(db: Session = Depends(get_db)):
    result = (
        db.query(
            func.sum(Bottle.bottle_count).label("total_count"),
            func.sum(Bottle.bottle_weight).label("total_weight")
        )
        .join(Machine, Bottle.machine_id == Machine.id)
        .all()
    )

    if not result:
        raise HTTPException(status_code=404, detail="No bottles found")

    total_count, total_weight = result[0]

    return {
        "total_count": total_count or 0,
        "total_weight": total_weight or 0.0
    }


@router.get("/my-bottle-stats", response_model=Dict[str, float],  dependencies=[Depends(verify_token)], tags=["Bottles"])
async def get_bottle_stats(db: Session = Depends(get_db), current_user: User = Depends(verify_token)):
    # Get the user's business by their ID
    business = db.query(Business).filter(Business.business_owner == current_user["id"]).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found for the user")

    # Get the machine IDs that belong to this business
    machine_ids = db.query(Machine.id).filter(Machine.business_id == business.id).all()
    
    if not machine_ids:
        raise HTTPException(status_code=404, detail="No machines found for this business")

    # Query for the total count and total weight of bottles for the machines of the current user's business
    result = (
        db.query(
            func.sum(Bottle.bottle_count).label("total_count"),
            func.sum(Bottle.bottle_weight).label("total_weight")
        )
        .filter(Bottle.machine_id.in_([machine_id[0] for machine_id in machine_ids]))  # Filter by machines belonging to the user's business
        .all()
    )

    # If no bottles are found, return zero values
    if not result:
        raise HTTPException(status_code=404, detail="No bottles found for this business")

    total_count, total_weight = result[0]

    return {
        "total_count": total_count or 0,  # Return 0 if no count is found
        "total_weight": total_weight or 0.0  # Return 0.0 if no weight is found
    }