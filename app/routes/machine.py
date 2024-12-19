from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Machine, User
from app.schemas import MachineCreate
from app.database import get_db
from datetime import datetime
from app.core.security import role_required, verify_token

router = APIRouter()

# Create a new machine
@router.post("/create_machines/", dependencies=[Depends(verify_token)])
async def create_machine(
    machine: MachineCreate,
    db: Session = Depends(get_db),
):
    # Check if the owner exists
    owner = db.query(User).filter(User.id == machine.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="User (owner) not found")

    # Create a new machine
    db_machine = Machine(
        name=machine.name,
        number=machine.number,
        street=machine.street,
        city=machine.city,
        state=machine.state,
        pin_code=machine.pin_code,
        owner_id=machine.owner_id,
        created_by=machine.created_by,
        updated_by=machine.updated_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

# Get all machines
@router.get("/machines/", dependencies=[Depends(verify_token)])
async def get_all_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    machines = db.query(Machine).offset(skip).limit(limit).all()
    return machines

# Get a machine by ID
@router.get("/machine/{machine_id}", dependencies=[Depends(verify_token)])
async def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

# Update a machine
@router.put("/machines/{machine_id}", dependencies=[Depends(verify_token)])
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
    db_machine.owner_id = machine.owner_id
    db_machine.updated_by = machine.updated_by
    db_machine.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_machine)
    return db_machine

# Delete a machine
@router.delete("/machines/{machine_id}", dependencies=[Depends(verify_token)])
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