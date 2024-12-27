import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from contextlib import asynccontextmanager
from app.database import engine, Base, SessionLocal  # Import engine and Base
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.admin import router as admin_router
from app.routes.business import router as business_router
from app.routes.machine import router as machine_router
from app.routes.bottles import router as bottle_router
from app.database import database  # Import the database instance

# Create database tables
Base.metadata.create_all(bind=engine)


# Create the FastAPI app instance
app = FastAPI()


# Include the user routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(business_router)
app.include_router(machine_router)
app.include_router(bottle_router)


# Connect to the database on app startup
@app.on_event("startup")
async def startup():
    # Connect to PostgreSQL database
    await database.connect()

# Disconnect from the database on app shutdown
@app.on_event("shutdown")
async def shutdown():
    # Disconnect from the database
    await database.disconnect()

@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI app with SQLite!"}

# Enable running with Uvicorn for local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",  # Use the app instance defined above
        host=os.getenv("HOST", "127.0.0.1"),  # Default to localhost
        port=int(os.getenv("PORT", 8000)),    # Default to port 8000
        reload=True                           # Enable auto-reload for development
    )
