from fastapi import APIRouter, Depends, HTTPException, security, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import auth
from models.auth_models import User, OTP
from schemas.auth_schemas import OTPRequest, OTPVerifyRequest, AuthResponse
from database import get_db
from sms_service import sms_service
from config import settings
from security import create_access_token, create_refresh_token

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number"""
    
    # Generate OTP
    otp_code = auth.generate_otp()
    hashed_otp = auth.hash_otp(otp_code)
    
    # Calculate expiry time
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    # Store OTP in database
    db_otp = OTP(
        phone_number=request.phone_number,
        hashed_otp=hashed_otp,
        expires_at=expire_time
    )
    db.add(db_otp)
    db.commit()
    
    # Send SMS
    success = sms_service.send_otp(request.phone_number, otp_code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again later."
        )
    
    return {"message": "OTP sent successfully", "expires_in_minutes": settings.OTP_EXPIRE_MINUTES}

@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and return JWT tokens"""
    
    # Find the most recent valid OTP for this phone number
    otp_record = db.query(OTP).filter(
        OTP.phone_number == request.phone_number,
        OTP.is_used == False,
        OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(OTP.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Verify OTP
    if not auth.verify_otp(request.otp, otp_record.hashed_otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Mark OTP as used
    otp_record.is_used = True
    
    # Create or get user
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not user:
        user = User(phone_number=request.phone_number, is_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send welcome message for new users
        sms_service.send_welcome_message(request.phone_number)
    else:
        user.is_verified = True
        user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Generate JWT tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        phone_number=user.phone_number,
        is_verified=user.is_verified
    )

@router.post("/refresh-token", response_model=dict)
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # Generate new access token
    access_token = security.create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }