from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional

# Import local modules
from models.delivery_models import DeliveryAgent, DeliveryAgentStatus
from models.order_models import Order, OrderStatus
from models.auth_models import User
from schemas.delivery_schemas import (
    DeliveryAgentCreate, DeliveryAgentUpdate, DeliveryAgentResponse,
    DeliveryAgentListResponse, LocationUpdate, DeliveryAssignment,
    DeliveryStatusUpdate
)
import auth
from database import get_db
from sms_service import sms_service

router = APIRouter(
    prefix="/api/delivery",
    tags=["Delivery Management"]
)

@router.post("/agents", response_model=DeliveryAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_agent(
    agent_data: DeliveryAgentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Create a new delivery agent (admin only)"""
    # In a real app, you'd check if the current user has admin privileges
    # For now, we'll allow any authenticated user to create agents
    
    # Check if phone number already exists
    existing_agent = db.query(DeliveryAgent).filter(DeliveryAgent.phone == agent_data.phone).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery agent with this phone number already exists"
        )
    
    db_agent = DeliveryAgent(**agent_data.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return db_agent

@router.get("/agents", response_model=DeliveryAgentListResponse)
async def get_delivery_agents(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by agent status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get list of delivery agents with pagination and filtering"""
    # Build query
    query = db.query(DeliveryAgent).filter(DeliveryAgent.is_active == True)
    
    # Apply status filter
    if status_filter:
        try:
            agent_status = DeliveryAgentStatus(status_filter)
            query = query.filter(DeliveryAgent.current_status == agent_status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    agents = query.order_by(DeliveryAgent.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return DeliveryAgentListResponse(
        delivery_agents=agents,
        total=total,
        page=page,
        size=size
    )

@router.get("/agents/{agent_id}", response_model=DeliveryAgentResponse)
async def get_delivery_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get details of a specific delivery agent"""
    agent = db.query(DeliveryAgent).filter(
        DeliveryAgent.id == agent_id,
        DeliveryAgent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found")
    
    return agent

@router.patch("/agents/{agent_id}", response_model=DeliveryAgentResponse)
async def update_delivery_agent(
    agent_id: int,
    agent_update: DeliveryAgentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update delivery agent information"""
    agent = db.query(DeliveryAgent).filter(
        DeliveryAgent.id == agent_id,
        DeliveryAgent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found")
    
    # Update agent fields
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    # Update timestamp
    agent.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(agent)
    
    return agent

@router.post("/agents/{agent_id}/location", response_model=DeliveryAgentResponse)
async def update_agent_location(
    agent_id: int,
    location: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update delivery agent's current location"""
    agent = db.query(DeliveryAgent).filter(
        DeliveryAgent.id == agent_id,
        DeliveryAgent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found")
    
    # Update location
    agent.current_latitude = location.latitude
    agent.current_longitude = location.longitude
    agent.last_location_update = datetime.now(timezone.utc)
    agent.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(agent)
    
    return agent

@router.post("/agents/{agent_id}/status", response_model=DeliveryAgentResponse)
async def update_agent_status(
    agent_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update delivery agent's status (available, assigned, offline)"""
    agent = db.query(DeliveryAgent).filter(
        DeliveryAgent.id == agent_id,
        DeliveryAgent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found")
    
    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")
    
    try:
        agent_status = DeliveryAgentStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    
    agent.current_status = agent_status
    agent.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(agent)
    
    return agent

@router.post("/assign", response_model=dict)
async def assign_delivery_agent(
    assignment: DeliveryAssignment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Assign a delivery agent to an order"""
    # Get the order
    order = db.query(Order).filter(Order.id == assignment.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check if order is in a state that can be assigned
    if order.status not in [OrderStatus.CONFIRMED, OrderStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be assigned at this stage"
        )
    
    # Get the delivery agent
    agent = db.query(DeliveryAgent).filter(
        DeliveryAgent.id == assignment.delivery_agent_id,
        DeliveryAgent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found")
    
    # Check if agent is available
    if agent.current_status != DeliveryAgentStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery agent is not available"
        )
    
    # Assign the agent to the order
    order.delivery_agent_id = assignment.delivery_agent_id
    order.status = OrderStatus.DISPATCHED
    order.updated_at = datetime.now(timezone.utc)
    
    # Update agent status
    agent.current_status = DeliveryAgentStatus.ASSIGNED
    agent.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Send SMS notifications
    # Notify delivery agent
    sms_service.send_delivery_assignment_sms(
        agent_phone=agent.phone,
        order_id=order.id,
        order_number=order.order_number
    )
    
    # Notify customer
    customer = db.query(User).filter(User.id == order.customer_id).first()
    if customer:
        sms_service.send_delivery_update_sms(
            customer_phone=customer.phone_number,
            order_id=order.id,
            status="dispatched",
            order_number=order.order_number
        )
    
    return {
        "message": "Delivery agent assigned successfully",
        "order_id": order.id,
        "agent_id": agent.id,
        "order_status": order.status.value
    }

@router.post("/orders/{order_id}/status", response_model=dict)
async def update_delivery_status(
    order_id: str,
    status_update: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update delivery status of an order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Store old status for SMS notification
    old_status = order.status
    
    # Update order status
    order.status = status_update.status
    if status_update.estimated_delivery_time:
        order.estimated_delivery_time = status_update.estimated_delivery_time
    
    # Set actual delivery time if status is delivered
    if status_update.status == OrderStatus.DELIVERED:
        order.actual_delivery_time = datetime.now(timezone.utc)
    
    order.updated_at = datetime.now(timezone.utc)
    
    # If order is delivered, make agent available again
    if status_update.status == OrderStatus.DELIVERED and order.delivery_agent_id:
        agent = db.query(DeliveryAgent).filter(DeliveryAgent.id == order.delivery_agent_id).first()
        if agent:
            agent.current_status = DeliveryAgentStatus.AVAILABLE
            agent.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Send SMS notifications
    customer = db.query(User).filter(User.id == order.customer_id).first()
    if customer and status_update.status != old_status:
        sms_service.send_delivery_update_sms(
            customer_phone=customer.phone_number,
            order_id=order.id,
            status=status_update.status.value,
            order_number=order.order_number
        )
    
    return {
        "message": "Delivery status updated successfully",
        "order_id": order.id,
        "status": status_update.status.value
    }

@router.get("/orders/pending", response_model=List[dict])
async def get_pending_deliveries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get list of orders pending delivery assignment"""
    pending_orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PENDING]),
        Order.delivery_agent_id.is_(None)
    ).all()
    
    return [
        {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
            "estimated_delivery_time": order.estimated_delivery_time
        }
        for order in pending_orders
    ]
