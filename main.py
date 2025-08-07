# main.py

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone # Import timezone

# Import all your project modules
import models
import schemas
import auth # Import the whole module
from database import engine, get_db
from sms_service import sms_service

# This line creates the database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Food Delivery App - Login API",
    description="Phone number verification system with OTP for food delivery app",
    version="1.0.0"
)

# --- Reusable Helper Function to Keep Code DRY ---

def _create_and_send_otp(phone_number: str, db: Session) -> bool:
    """Generates, stores, and sends an OTP, returning success status."""
    otp_code = auth.generate_otp()
    otp_hash = auth.hash_otp(otp_code)
    # Use timezone-aware datetime
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Delete any existing unused OTPs for this number to invalidate old ones
    db.query(models.OTP).filter(
        models.OTP.phone_number == phone_number,
        models.OTP.is_used == False
    ).delete()
    
    # Store the new OTP record
    db_otp = models.OTP(phone_number=phone_number, hashed_otp=otp_hash, expires_at=expires_at)
    db.add(db_otp)
    db.commit()
    
    # Send OTP via SMS and return the result
    return sms_service.send_otp(phone_number= phone_number, otp=otp_code)

# --- API Endpoints ---

@app.post("/auth/login", response_model=schemas.LoginResponse)
async def login(request: schemas.OTPRequest, db: Session = Depends(get_db)):
    """
    Finds or creates a user, then sends an OTP to their phone number.
    """
    user = db.query(models.User).filter(models.User.phone_number == request.phone_number).first()
    if not user:
        user = models.User(phone_number=request.phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)

    if not _create_and_send_otp(request.phone_number, db):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again later."
        )

    return schemas.LoginResponse(
        message="OTP sent successfully to your phone number",
        phone_number=request.phone_number
    )

@app.post("/auth/verify-otp", response_model=schemas.Token)
async def verify_otp_endpoint(request: schemas.OTPVerify, db: Session = Depends(get_db)):
    """
    Verifies an OTP and returns a JWT access token upon success.
    """
    otp_record = db.query(models.OTP).filter(
        models.OTP.phone_number == request.phone_number,
        models.OTP.is_used == False,
        models.OTP.expires_at > datetime.now(timezone.utc) # Use timezone-aware
    ).order_by(models.OTP.created_at.desc()).first()

    if not otp_record or not auth.verify_otp(request.otp, otp_record.hashed_otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP.")

    otp_record.is_used = True
    
    user = db.query(models.User).filter(models.User.phone_number == request.phone_number).first()
    if user:
        user.is_verified = True
    
    db.commit()
    
    # Create access token for the user's phone number ("sub" is for "subject")
    access_token = auth.create_access_token(data={"sub": request.phone_number})
    
    # Optionally send a welcome message
    sms_service.send_welcome_message(request.phone_number)
    
    return schemas.Token(access_token=access_token, token_type="bearer")

@app.post("/auth/resend-otp", response_model=schemas.LoginResponse)
async def resend_otp(request: schemas.OTPRequest, db: Session = Depends(get_db)):
    """
    Resends an OTP to a registered phone number.
    """
    user = db.query(models.User).filter(models.User.phone_number == request.phone_number).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not registered. Please use the login endpoint first."
        )

    if not _create_and_send_otp(request.phone_number, db):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again later."
        )

    return schemas.LoginResponse(
        message="OTP resent successfully to your phone number",
        phone_number=request.phone_number
    )

@app.get("/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(auth.get_current_user), # Using our new dependency
    db: Session = Depends(get_db)
):
    """
    Protected endpoint to get the current authenticated user's information.
    """
    phone_number = current_user.get("phone_number")
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.get("/")
async def root():
    return {"message": "Welcome to the Food Delivery App Login API"}