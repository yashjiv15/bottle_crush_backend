from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Machine, Bottle, User, Business
from app.schemas import BottleCreate
from app.database import get_db
from datetime import datetime
from app.core.security import get_current_user, verify_token
from sqlalchemy.orm import aliased
from sqlalchemy import false, func, cast, Date
from typing import Dict
import pytz


IST = pytz.timezone('Asia/Kolkata')

router = APIRouter()

@router.post("/create_bottle/", tags=["Admin-Bottle"])
async def create_bottle(
    bottle: BottleCreate,  # Assuming you have a Pydantic model BottleCreate
    db: Session = Depends(get_db)
):
    # Check if the machine exists
    machine = db.query(Machine).filter(Machine.id == bottle.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    current_time_ist = datetime.now(IST)
    business_id = machine.business_id

    # Create a new bottle entry
    db_bottle = Bottle(
        machine_id=bottle.machine_id,
        bottle_count=bottle.bottle_count,
        bottle_weight=bottle.bottle_weight,
        created_by=business_id,  # Use the business_id from the machine
        updated_by=business_id,
        created_at=current_time_ist,  # Set created_at to current time in IST
        updated_at=current_time_ist 
    )
    db.add(db_bottle)
    db.commit()
    db.refresh(db_bottle)
    return db_bottle


@router.get("/bottles/",  dependencies=[Depends(verify_token)], tags=["Admin-Bottle"])
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


@router.get("/bottle/{bottle_id}",  dependencies=[Depends(verify_token)], tags=["Admin-Bottle"])
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

@router.get("/bottle-stats", response_model=Dict[str, float],  dependencies=[Depends(verify_token)], tags=["Admin-Dashboard"])
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


@router.get("/my-bottle-stats", response_model=Dict[str, float],  dependencies=[Depends(verify_token)], tags=["Customer-Dashboard"])
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

@router.get("/my-daywise-bottle-stats", dependencies=[Depends(verify_token)], tags=["Customer-Dashboard"])
async def get_daywise_bottle_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Fetch current user
):
    """
    Get day-wise count and weight of bottles per machine for the current user's business.
    """
    # Fetch the business ID from the current user
    business_owner = current_user["id"]  # Assuming the current user has a business_id attribute
    print(business_owner)
    # Validate if the business exists
    business = db.query(Business).filter(Business.business_owner == business_owner).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Get all machines for the business
    machines = db.query(Machine).filter(Machine.business_id == business.id).all()
    
    # Query to calculate day-wise bottle stats with left join
    stats = (
        db.query(
            cast(Bottle.created_at, Date).label("date"),  # Extract date from timestamp
            Machine.id.label("machine_id"),
            Machine.name.label("machine_name"),
            func.coalesce(func.sum(Bottle.bottle_count), 0).label("total_bottles"),  # Handle no bottles case
            func.coalesce(func.sum(Bottle.bottle_weight), 0.0).label("total_weight"),  # Handle no weight case
        )
        .join(Machine, Bottle.machine_id == Machine.id, isouter=True)  # Left join to include machines without bottles
        .filter(Machine.business_id == business.id)  # Filter by business ID from the current user
        .group_by(cast(Bottle.created_at, Date), Machine.id)  # Group by date and machine
        .order_by(cast(Bottle.created_at, Date).desc(), Machine.id)  # Sort by date and machine
        .all()
    )

    # Format the result
    result = {}
    for stat in stats:
        date = stat.date.isoformat()  # Format date as string
        if date not in result:
            result[date] = []

        # Add machine details
        result[date].append(
            {
                "machine_id": stat.machine_id,
                "machine_name": stat.machine_name,
                "total_bottles": stat.total_bottles,
                "total_weight": stat.total_weight,
            }
        )

    # Ensure machines with no records are included with zero values
    for machine in machines:
        for date in result:
            # If the machine is not in the day-wise records, add it with zero values
            if not any(m["machine_id"] == machine.id for m in result[date]):
                result[date].append(
                    {
                        "machine_id": machine.id,
                        "machine_name": machine.name,
                        "total_bottles": 0,
                        "total_weight": 0.0,
                    }
                )

    return result

@router.get("/daywise-bottle-stats", dependencies=[Depends(verify_token)], tags=["Admin-Dashboard"])
async def get_daywise_bottle_stats_all_businesses(
    db: Session = Depends(get_db),
):
    """
    Get day-wise count and weight of bottles per machine for all businesses.
    """
    # Query to calculate day-wise bottle stats for all businesses
    stats = (
        db.query(
            cast(Bottle.created_at, Date).label("date"),  # Extract date from timestamp
            Machine.id.label("machine_id"),
            Machine.name.label("machine_name"),
            func.coalesce(func.sum(Bottle.bottle_count), 0).label("total_bottles"),  # Handle no bottles case
            func.coalesce(func.sum(Bottle.bottle_weight), 0.0).label("total_weight"),  # Handle no weight case
            Business.name.label("business_name")  # Get business name
        )
        .join(Machine, Bottle.machine_id == Machine.id, isouter=True)  # Left join to include machines without bottles
        .join(Business, Machine.business_id == Business.id)  # Join with Business table
        .group_by(cast(Bottle.created_at, Date), Machine.id, Business.id)  # Group by date, machine, and business
        .order_by(cast(Bottle.created_at, Date).desc(), Machine.id)  # Sort by date and machine
        .all()
    )

    # Format the result
    result = {}
    for stat in stats:
        if stat.date is not None:
            date = stat.date.isoformat()  # Format date as string
            business_name = stat.business_name
            if date not in result:
               result[date] = {}

            if business_name not in result[date]:
               result[date][business_name] = []

            result[date][business_name].append(
                {
                "machine_id": stat.machine_id,
                "machine_name": stat.machine_name,
                "total_bottles": stat.total_bottles,
                "total_weight": stat.total_weight,
                }
            )
        else:
            print("Warning: Found a stat with None date:", stat)

    # Now, ensure all machines are included for each business even if they don't have bottle records
    # Get all machines for each business
    businesses = db.query(Business).all()
    for business in businesses:
        machines = db.query(Machine).filter(Machine.business_id == business.id).all()
        for date in result:
            if business.name not in result[date]:
                result[date][business.name] = []

            # Check if the machine is missing for this date, if so, add it with zero values
            for machine in machines:
                if not any(m["machine_id"] == machine.id for m in result[date][business.name]):
                    result[date][business.name].append(
                        {
                            "machine_id": machine.id,
                            "machine_name": machine.name,
                            "total_bottles": 0,
                            "total_weight": 0.0,
                        }
                    )

    return result
