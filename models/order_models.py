from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    Float,
    Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid

class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(20), unique=True, index=True, nullable=False)
    
    # Relationships to existing models
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivery_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    delivery_agent_id = Column(Integer, ForeignKey("delivery_agents.id"), nullable=True)
    
    # Order details
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_amount = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    subtotal = Column(Float, nullable=False)
    
    # Delivery details
    estimated_delivery_time = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_time = Column(DateTime(timezone=True), nullable=True)
    delivery_instructions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # customer = relationship("User", back_populates="orders")  # Commented out to avoid circular dependency
    delivery_address = relationship("Address")
    delivery_agent = relationship("DeliveryAgent")  # Removed back_populates to avoid circular dependency
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, nullable=False)  # Will reference restaurant system menu items
    
    # Item details
    item_name = Column(String(255), nullable=False)  # Store name at time of order
    item_price = Column(Float, nullable=False)  # Store price at time of order
    quantity = Column(Integer, nullable=False, default=1)
    special_instructions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    # menu_item relationship will be added when restaurant system is integrated
