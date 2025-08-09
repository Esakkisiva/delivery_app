# main.py

from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

from fastapi import FastAPI

# Import separated routers
from routers.auth_router import router as auth_router
from routers.address_router import router as address_router
from routers.order_router import router as order_router
from routers.delivery_router import router as delivery_router

# Import models to create tables
from models.auth_models import User, OTP
from models.address_models import Address
from models.order_models import Order, OrderItem
from models.delivery_models import DeliveryAgent
from database import engine

# Create DB tables
from database import Base
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="Food Delivery App - Complete API",
    description="Complete food delivery app with authentication, address management, order management, and delivery tracking",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(address_router)
app.include_router(order_router)
app.include_router(delivery_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Food Delivery App Login API"}
