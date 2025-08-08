# main.py

from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

from fastapi import FastAPI

# Import separated routers
from routers.auth_router import router as auth_router
from routers.address_router import router as address_router

# Import models to create tables
from models.auth_models import User, OTP
from models.address_models import Address
from database import engine

# Create DB tables
from database import Base
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="Food Delivery App - Login API",
    description="Phone number verification system with OTP for food delivery app",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(address_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Food Delivery App Login API"}
