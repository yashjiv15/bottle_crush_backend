import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from contextlib import asynccontextmanager
from app.database import engine, Base, SessionLocal  # Import engine and Base
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.admin import router as admin_router, create_superadmin
from app.routes.business import router as business_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Create the FastAPI app instance
app = FastAPI()


# Include the user routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(business_router)


@app.on_event("startup")
async def startup_event():
    # Run the create_superadmin function at startup
    db = SessionLocal()
    create_superadmin(db)
    db.close()


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
