from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from databases import Database
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE")

# Create a Database connection instance
database = Database(DATABASE_URL)

# Define a base class for SQLAlchemy models
Base = declarative_base()

# Configure the SQLAlchemy engine with connection pooling parameters
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    pool_size=10,  # Default pool size (adjust based on application needs)
    max_overflow=20,  # Maximum overflow connections beyond the pool size
    pool_timeout=30,  # Maximum time (seconds) to wait for a connection
    pool_recycle=1800,  # Recycle connections after 30 minutes (prevent stale connections)
    pool_pre_ping=True  # Test connections before using them
)

# Create a session maker for SQLAlchemy ORM
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
