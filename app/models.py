from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary, TIMESTAMP, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base, engine  # Assuming you import these from your project
from datetime import datetime

# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="r_customer", nullable=False)
    reset_otp = Column(String, nullable=True)
    reset_otp_expiration = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

# Business Model
class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    mobile = Column(String, unique=True, nullable=False)
    logo_image = Column(LargeBinary, nullable=True)
    business_owner = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    business_user = relationship("User", foreign_keys=[business_owner])
    created_user = relationship("User", foreign_keys=[created_by])
    updated_user = relationship("User", foreign_keys=[updated_by])

# Machine Model
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
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    business = relationship("Business", foreign_keys=[business_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

# Bottle Model
class Bottle(Base):
    __tablename__ = "bottles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    bottle_count = Column(Integer, nullable=False)
    bottle_weight = Column(Float, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])

# Create the tables in the database
Base.metadata.create_all(bind=engine)
