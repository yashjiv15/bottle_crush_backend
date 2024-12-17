# models.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Create an instance of the base class for models
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="r_customer")  # Add the role field
    is_active = Column(Boolean, default=False) 
    is_deleted = Column(Boolean, default=False) 


# Connect to SQLite and create a database session
DATABASE_URL = "sqlite:///./bottle_crush.db"  # You can change this to your preferred SQLite database path

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the database (if not already created)
Base.metadata.create_all(bind=engine)
