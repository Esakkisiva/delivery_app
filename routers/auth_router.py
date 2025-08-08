from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

# Import local modules
from models.auth_models import User, OTP
from schemas.auth_schemas import OTPRequest, OTPVerify, LoginResponse, Token, UserResponse
import auth
from database import get_db
from sms_service import sms_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- Reusable Helper Function ---
def _create_and_send_otp(phone_number: str, db: Session) -> bool:
    """Generates, stores, and sends an OTP, returning success status."""
    otp_code = auth.generate_otp()
    otp_hash = auth.hash_otp(otp_code)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Remove old unused OTPs for this phone
    db.query(OTP).filter(
        OTP.phone_number == phone_number,
        OTP.is_used == False
    ).delete()

    # Store the new OTP
    db_otp = OTP(
        phone_number=phone_number,
        hashed_otp=otp_hash,
        expires_at=expires_at
    )
    db.add(db_otp)
    db.commit()

    # Send OTP via SMS
    return sms_service.send_otp(phone_number=phone_number, otp=otp_code)

@router.post("/login", response_model=LoginResponse)
async def login(request: OTPRequest, db: Session = Depends(get_db)):
    """Finds or creates a user, then sends an OTP."""
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not user:
        user = User(phone_number=request.phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)

    if not _create_and_send_otp(request.phone_number, db):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again later."
        )

    return LoginResponse(
        message="OTP sent successfully to your phone number",
        phone_number=request.phone_number
    )

@router.post("/verify-otp", response_model=Token)
async def verify_otp_endpoint(request: OTPVerify, db: Session = Depends(get_db)):
    """Verifies an OTP and returns a JWT access token."""
    otp_record = db.query(OTP).filter(
        OTP.phone_number == request.phone_number,
        OTP.is_used == False,
        OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record or not auth.verify_otp(request.otp, otp_record.hashed_otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP.")

    otp_record.is_used = True

    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if user:
        user.is_verified = True

    db.commit()

    # Create access token
    access_token = auth.create_access_token(data={"sub": request.phone_number})

    # Send welcome message
    sms_service.send_welcome_message(request.phone_number)

    return Token(access_token=access_token, token_type="bearer")

@router.post("/resend-otp", response_model=LoginResponse)
async def resend_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Resends an OTP to a registered phone number."""
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
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

    return LoginResponse(
        message="OTP resent successfully to your phone number",
        phone_number=request.phone_number
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Returns current authenticated user's information."""
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
