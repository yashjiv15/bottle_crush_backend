from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from databases import Database
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

# Define the SQLite database URL
DATABASE_URL = "postgresql://postgres:Eagle%2310@localhost:5432/bottle_crush"

# Create a Database connection instance
database = Database(DATABASE_URL)

# Define a base class for SQLAlchemy models
Base = declarative_base()

# Create a session maker for SQLAlchemy ORM
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()