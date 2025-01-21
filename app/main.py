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
from app.routes.email import router as email_router
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
app.include_router(email_router)


if __name__ == "__main__":
    import asyncio

    async def test_connection():
        try:
            await database.connect()
            print("Successfully connected to MySQL!")
            await database.disconnect()
        except Exception as e:
            print(f"Connection failed: {e}")

    asyncio.run(test_connection())
