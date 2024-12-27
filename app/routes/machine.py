from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
<<<<<<< HEAD
from app.models import Machine, Business, User, Bottle
from app.schemas import MachineCreate
=======
from app.models import Machine, Business, User
from app.schemas import MachineCreate, MachinesPerBusiness
>>>>>>> 2c5dcfe6320886c89a27c05706b7cec37e659971
from app.database import get_db
from datetime import datetime
from app.core.security import role_required, verify_token
from sqlalchemy.orm import aliased
<<<<<<< HEAD
from sqlalchemy import func
from typing import Dict, List
=======
from typing import List
>>>>>>> 2c5dcfe6320886c89a27c05706b7cec37e659971

router = APIRouter()

# Create a new machine
@router.post("/create_machines/", dependencies=[Depends(verify_token)], tags=["Machines"])
async def create_machine(
    machine: MachineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("t_admin"))
):
    # Check if the owner exists
    business = db.query(Business).filter(Business.id == machine.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business (business) not found")

    # Create a new machine
    db_machine = Machine(
        name=machine.name,
        number=machine.number,
        street=machine.street,
        city=machine.city,
        state=machine.state,
        pin_code=machine.pin_code,
        business_id=machine.business_id,
        created_by=current_user["id"],  # Changed from current_user.id
        updated_by=current_user["id"],  # Changed from current_user.id
    )
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

# Get all machines
@router.get("/machines/", dependencies=[Depends(verify_token)], tags=["Machines"])
async def get_all_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # Query all machines with business name and user names
    machines = (
        db.query(
            Machine.id,
            Machine.name,
            Machine.number,
            Machine.street,
            Machine.city,
            Machine.state,
            Machine.pin_code,
            Business.name.label("business_name"),
            User.email.label("creator_name"),
            User.email.label("updater_name"),
            Machine.created_at,
            Machine.updated_at,
        )
        .join(Business, Machine.business_id == Business.id)
        .join(User, Machine.created_by == User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Format the result
    return [
        {
            "id": machine.id,
            "name": machine.name,
            "number": machine.number,
            "street": machine.street,
            "city": machine.city,
            "state": machine.state,
            "pin_code": machine.pin_code,
            "business_name": machine.business_name,
            "creator_name": machine.creator_name,
            "updater_name": machine.updater_name,
            "created_at": machine.created_at,
            "updated_at": machine.updated_at,
        }
        for machine in machines
    ]


# Get a machine by ID
@router.get("/machine/{machine_id}", dependencies=[Depends(verify_token)], tags=["Machines"])
async def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
):
    # Create aliases for the User table to join it twice
    creator = aliased(User)
    updater = aliased(User)

    # Query machine with related business and user details
    machine = (
        db.query(
            Machine.id,
            Machine.name,
            Machine.number,
            Machine.street,
            Machine.city,
            Machine.state,
            Machine.pin_code,
            Business.name.label("business_name"),
            creator.email.label("creator_name"),
            updater.email.label("updater_name"),
            Machine.created_at,
            Machine.updated_at,
        )
        .join(Business, Machine.business_id == Business.id)
        .join(creator, Machine.created_by == creator.id)
        .join(updater, Machine.updated_by == updater.id)
        .filter(Machine.id == machine_id)
        .first()
    )

    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Format and return the result
    return {
        "id": machine.id,
        "name": machine.name,
        "number": machine.number,
        "street": machine.street,
        "city": machine.city,
        "state": machine.state,
        "pin_code": machine.pin_code,
        "business_name": machine.business_name,
        "creator_name": machine.creator_name,
        "updater_name": machine.updater_name,
        "created_at": machine.created_at,
        "updated_at": machine.updated_at,
    }
# Update a machine
@router.put("/machines/{machine_id}", dependencies=[Depends(verify_token)], tags=["Machines"])
async def update_machine(
    machine_id: int,
    machine: MachineCreate,
    db: Session = Depends(get_db),
):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Update machine details
    db_machine.name = machine.name
    db_machine.number = machine.number
    db_machine.street = machine.street
    db_machine.city = machine.city
    db_machine.state = machine.state
    db_machine.pin_code = machine.pin_code
    db_machine.business_id = machine.business_id
    db_machine.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_machine)
    return db_machine

# Delete a machine
@router.delete("/machines/{machine_id}", dependencies=[Depends(verify_token)] , tags=["Machines"])
async def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db),
):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    db.delete(db_machine)
    db.commit()
    return db_machine

<<<<<<< HEAD
@router.get("/machines-count", response_model=int, tags=["Machines"])
async def get_total_machines_count(db: Session = Depends(get_db)):
    # Query to get the total count of machines
    machine_count = db.query(func.count(Machine.id)).scalar()

    if machine_count is None:
        raise HTTPException(status_code=404, detail="No machines found")

    return machine_count


@router.get("/machines/bottle-count", response_model=List[Dict[str, int]], tags=["Machines"])
async def get_bottle_count_per_machine(db: Session = Depends(get_db)):
    # Query the total bottle count per machine
    result = (
        db.query(
            Bottle.machine_id,
            func.sum(Bottle.bottle_count).label("total_bottle_count")
        )
        .group_by(Bottle.machine_id)  # Group by machine_id to get counts for each machine
        .join(Machine, Bottle.machine_id == Machine.id)  # Join with Machine to get machine details if needed
        .all()  # Fetch all results
    )

    # If no bottles are found, return an empty list
    if not result:
        raise HTTPException(status_code=404, detail="No bottles found")

    # Format and return the result
    return [
        {"machine_id": machine_id, "total_bottle_count": total_bottle_count or 0}
        for machine_id, total_bottle_count in result
    ]
=======
@router.get("/my-machines", response_model=List[MachinesPerBusiness], dependencies=[Depends(verify_token)], tags=["Machines"])
async def get_machines_by_business(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    """
    Fetch all machines associated with the current user's business.
    The user's business is fetched based on the JWT token.
    """
    user_id = payload.get("id")  # Assuming you store user_id in the token payload
    # Fetch the business owned by the current user
    business = db.query(Business).filter(Business.business_owner == user_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found for the user")
    
    # Fetch all machines associated with this business
    machines = db.query(Machine).filter(Machine.business_id == business.id).all()

    if not machines:
        raise HTTPException(status_code=404, detail="No machines found for this business")

    return machines
>>>>>>> 2c5dcfe6320886c89a27c05706b7cec37e659971
