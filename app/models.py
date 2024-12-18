# models.py
from sqlalchemy import  Column, Integer, String, Boolean, DateTime, ForeignKey
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

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="r_customer")  # Add the role field
    is_active = Column(Boolean, default=False) 
    is_deleted = Column(Boolean, default=False) 

# Business Model
class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    mobile = Column(String, nullable=False, unique=True)
    logo_image = Column(String, nullable=False)  # This will store the logo image path
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to User model
    created_user = relationship("User", foreign_keys=[created_by])
    updated_user = relationship("User", foreign_keys=[updated_by])

# Create the tables in the database (if not already created)
Base.metadata.create_all(bind=engine)
