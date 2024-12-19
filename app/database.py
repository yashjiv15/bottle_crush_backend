from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Define the SQLite database URL
DATABASE_URL = "sqlite:///./bottle_crush.db"

# Create the engine for SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a SessionLocal class to create new sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define a Base class for declarative models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()