from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Float,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class DeliveryAgentStatus(enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    OFFLINE = "offline"

class DeliveryAgent(Base):
    __tablename__ = "delivery_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True)
    
    # Status and location
    current_status = Column(Enum(DeliveryAgentStatus), default=DeliveryAgentStatus.OFFLINE, nullable=False)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    
    # Agent details
    is_active = Column(Boolean, default=True)
    vehicle_type = Column(String(50), nullable=True)  # bike, car, etc.
    vehicle_number = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # orders = relationship("Order", back_populates="delivery_agent")  # Commented out to avoid circular dependency
