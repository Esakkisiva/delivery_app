# models.py (Corrected)

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

# ... (User and OTP models are fine) ...
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    addresses = relationship("Address", back_populates="owner")

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), index=True, nullable=False)
    hashed_otp = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)


class Address(Base):
    __tablename__ = "addresses"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    country = Column(String(50), default="India")
    full_name = Column(String(100), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    flat_house_building = Column(String(255), nullable=False)
    area_street_sector = Column(String(255), nullable=False)
    landmark = Column(String(255), nullable=True)
    pincode = Column(String(10), nullable=False)
    town_city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # --- FIX IS HERE ---
    # OLD LINE: updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Add `server_default` so it gets a value on creation as well.
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="addresses")