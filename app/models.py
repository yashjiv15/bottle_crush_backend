# models.py
from sqlalchemy import  Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.database import Base, engine  # Import Base and engine
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func

# Define the User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="r_customer")  # Add the role field
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=False) 
    is_deleted = Column(Boolean, default=False) 

# Business Model
class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    mobile = Column(String, nullable=False, unique=True)
    logo_image = Column(LargeBinary, nullable=True)
    business_owner = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to User model
    business_user = relationship("User", foreign_keys=[business_owner])
    created_user = relationship("User", foreign_keys=[created_by])
    updated_user = relationship("User", foreign_keys=[updated_by])


class Machine(Base):
    __tablename__ = 'machines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    number = Column(String, nullable=False)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin_code = Column(String, nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", foreign_keys=[business_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

# Create the tables in the database (if not already created)
Base.metadata.create_all(bind=engine)
