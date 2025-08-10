from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Comment out relationship to avoid circular dependency
    # owner = relationship("User", back_populates="addresses")
