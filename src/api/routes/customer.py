"""Customer API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ...models.db_session import get_db
from ...models.schemas import OrderResponse

router = APIRouter(prefix="/customer", tags=["customer"])
logger = logging.getLogger(__name__)


@router.get("/orders", response_model=List[OrderResponse])
async def get_customer_orders(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Get all orders for a customer by phone number.
    
    Args:
        phone: Customer phone number
        db: Database session
        
    Returns:
        List of orders for the customer
    """
    try:
        from ...models.database import Order as OrderModel, Customer
        
        # Find customer by phone first
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer:
            logger.info(f"No customer found for phone {phone}")
            return []
        
        # Query orders by customer_id
        orders = db.query(OrderModel).filter(
            OrderModel.customer_id == customer.id
        ).order_by(OrderModel.created_at.desc()).all()
        
        logger.info(f"Retrieved {len(orders)} orders for customer {phone}")
        
        return orders
        
    except Exception as e:
        logger.error(f"Error retrieving orders for customer {phone}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve orders: {str(e)}")


@router.post("/orders/{order_id}/report-issue")
async def report_order_issue(
    order_id: str,
    issue_description: str,
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Report an issue with an order.
    
    Args:
        order_id: Order ID
        issue_description: Description of the issue
        phone: Customer phone number
        db: Database session
        
    Returns:
        Success message
    """
    try:
        from ...models.database import Order as OrderModel, Customer
        
        # Find customer by phone first
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Verify the order belongs to the customer
        order = db.query(OrderModel).filter(
            OrderModel.id == order_id,
            OrderModel.customer_id == customer.id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # For now, just log the complaint
        # In a real system, you'd create a complaint record
        logger.info(f"Order complaint received - Order: {order_id}, Customer: {phone}, Issue: {issue_description}")
        
        # You could add complaint to database here
        # complaint = ComplaintModel(
        #     order_id=order_id,
        #     customer_phone=phone,
        #     description=issue_description,
        #     status='open'
        # )
        # db.add(complaint)
        # db.commit()
        
        return {
            "message": "Issue reported successfully",
            "order_id": order_id,
            "status": "complaint_received"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reporting issue for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to report issue: {str(e)}")


@router.get("/orders/{order_id}/status")
async def get_order_status(
    order_id: str,
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed status of a specific order.
    
    Args:
        order_id: Order ID
        phone: Customer phone number
        db: Database session
        
    Returns:
        Order status details
    """
    try:
        from ...models.database import Order as OrderModel, Customer
        
        # Find customer by phone first
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Verify the order belongs to the customer
        order = db.query(OrderModel).filter(
            OrderModel.id == order_id,
            OrderModel.customer_id == customer.id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total": order.total,
            "created_at": order.created_at,
            "estimated_ready_time": order.estimated_ready_time,
            "items": order.items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving status for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve order status: {str(e)}")